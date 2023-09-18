from Value_util import StackValue


def append_operands(stack, num):
    assert isinstance(stack, list)
    assert isinstance(num, int), print(num)
    for i in range(num):
        _append_an_operand(stack)

def _append_an_operand(stack):
    assert isinstance(stack, list)
    new_val = StackValue.generate_value_with_any_type()
    new_val.generate_svalue()
    stack.append(new_val)
