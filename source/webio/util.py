from source.pywebio import output


def toast_succ(text="succ!", duration=2):
    output.toast(text, position='right', color='#2188ff', duration=duration)