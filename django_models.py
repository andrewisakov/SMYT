import datetime
from django.db import models
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def discounts(self, discount_date=datetime.datetime.now()):
        return Discount.objects.\
            filter(kind_id=self.pk).\
            filter(kind='DC').\
            filter(begin_datetime <= discount_date).\
            filter(end_datetime >= discount_date).get()


User.customer = property(lambda u: Customer.objects.get_or_create(user=u)[0])


class Order(models.Model):

    customer = models.ForeignKey(Customer)


class OrderState(models.Model):
    STATE_CHOICES = (('OC', 'Создан/Created'),
                     ('OD', 'Удалён/Deleted'),
                     ('IA', 'Товар добавлен/Item added'),
                     ('ID', 'Товар удалён/Item deleted'),
                     ('OP', 'Оплачен/Payed'),
                     ('OA', 'Подтверждён/Approved'),
                     ('OP', 'Отправлен/Posted'))

    state = models.CharField(verbose_name='Состояние', max_length=2, choices=STATE_CHOICES)
    order = models.ManyToManyField(Order, verbose_name='Заказ')
    item = models.ManyToManyField('Item', null=True)
    state_time = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        unique_togethers = (('order', 'state_time', ), )
        ordering = ['state_time', ]


class Discount(models.Model):
    DISCOUNT_CHOICES = (('DI', 'Скидка на товар/Item Discount'),
                        ('DB', 'Скидка на бренд/Brand Discount '),
                        ('DG', 'Скидка на группу(категорию)/Group Discount'),
                        ('DC', 'Скидка клиента/Client Discount'))

    begin_datetime = models.DateTimeField(
        null=True, verbose_name='Начало скидки', default=datetime.datetime.min)
    end_datetime = models.DateTimeField(
        null=True, verbose_name='Конец Скидки', default=datetime.datetime.max)
    kind = models.CharField(null=True, choices=DISCOUNT_CHOICES, max_length=2)
    kind_id = models.IntegerField()

    @property
    def period(self):
        return self.begin_datetime, self.end_datetime


class Brand(models.Model):
    name = models.CharField(verbose_name='Бренд', unique=True)

    def discounts(self, discount_datetime=datetime.datetime.now()):
        return Discount.objects.\
            filter(kind_id=self.pk).\
            filter(kind='DB').\
            filter(begin_datetime <= discount_datetime).\
            filter(end_datetime >= discount_datetime).get()


    class Meta:
        unique_togethers = (('name', ), )


class Group(models.Model):
    name = models.CharField(verbose_name='Категория')

    def discounts(self, discount_date=datetime.datetime.now()):
        return Discount.objects.\
            filter(kind_id=self.pk).\
            filter(kind='DG').\
            filter(begin_datetime <= discount_date).\
            filter(end_datetime >= discount_date).get()

    class Meta:
        unique_togethers = (('name', ), )


class ItemCosts(models.Model):
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    from_datetime = models.DateTimeField(auto_now=True, auto_now_add=True)  # Начало действия
    item = models.ForeignKey('Item', on_delete=models.CASCADE)  # N->1

    class Meta:
        ordering = ['-from_datetime', ]
        unique_togethers = (('item', 'from_datetime', ), )


class Item(models.Model):
    name = models.CharField(verbose_name='Наименование')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)  # N->1
    group = models.ForeignKey(Group, on_delete=models.CASCADE)  # N->1

    def discounts(self, discount_datetime=datetime.datetime.now()):
        return Discount.objects.\
            filter(kind_id=self.pk).\
            filter(kind='DI').\
            filter(begin_datetime <= discount_datetime).\
            filter(end_datetime >= discount_datetime).get()

    def price_current(self, from_datetime=datetime.datetime.now()):
        return ItemCosts.objects.\
            filter(item=self).\
            filter(from_datetime >= from_datetime).get()


class OrderItem(models.Model):
    item = models.OneToOneField(Item)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # Предполагаем, что весового товара не будет :)
    quantity = models.IntegerField(verbose_name='Количество', default=1)

    def discounts(self):
        item = self.item
        return (item.discounts(),
                item.brand.discounts(),
                item.group.discounts(), )


# Обработка сигналов

def _set_item_order_state(instance, state):
    order_state = OrderState(
        state=state.upper(),
        order=instance.order,
        item=instance.item)
    order_state.save()


def _set_order_state(instance, state):
    order_state = OrderState(state=state.upper(),
                             order=instance.order)
    order_state.save()


@receiver(post_delete, sender=OrderItem)
def order_item_post_delete(sender, instance):
    _set_order_state(instance, state='ID')


@receiver(post_save, sender=OrderItem)
def order_item_post_save(sender, instance):
    _set_item_order_state(instance, state='IA')


@receiver(post_delete, sender=Order)
def order_post_delete(sender, instance):
    _set_order_state(instance, state='OD')


@receiver(post_save, sender=Order)
def order_post_save(sender, instance):
    _set_order_state(instance, state='OC')
