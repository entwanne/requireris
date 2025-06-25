def match(s, pattern):
    i = 0
    if pattern == s:
        return 1
    ls = len(s)
    for i, cp in enumerate(pattern):
        if cp == '*':
            if match(s, pattern[:i] + pattern[i + 1:]):
                return 1
            if i < ls and match(s, pattern[:i] + s[i] + pattern[i:]):
                return 1
        elif i < ls and cp != s[i]:
            return 0
    return 0
