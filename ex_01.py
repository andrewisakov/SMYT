#!/usr/bin/python3

exs = 'esdfd((esdf)(esdf' #  -> 'esdfd((esdf)'

def select(s_base: str):
    result_p = len(s_base)
    close_brackets = 0
    for p in range(len(s_base)-1, -1, -1):
        # print(p, close_brackets, s_base[:result_p])
        if s_base[p] == ')':
            close_brackets += 1
        elif s_base[p] == '(':
            if close_brackets > 0:
                close_brackets -= 1
            else:
                result_p = p
    # print(result_p)
    return s_base[:result_p]


if __name__ == '__main__':
    print(select(exs))
