import libcst as cst

from extra_checks.fixes.fix_choices_constraint import gen_fix_for_choices_constraint

SOURCE = """
class TestClass(Token):
    class Meta:
        constraints = [
            models.CheckConstraint(name="value_valid", check=models.Q(value__in=[1, 2]))
        ]
    """


def test_fix_add():
    result = """
class TestClass(Token):
    class Meta:
        constraints = [
            models.CheckConstraint(name="value_valid", check=models.Q(value__in=[1, 2])), models.CheckConstraint(name="another_valid", check=models.Q(value__in=[1, 2, 3]))
        ]
    """

    source_tree = cst.parse_module(SOURCE)
    modefied_tree = source_tree.visit(
        gen_fix_for_choices_constraint(
            "TestClass",
            name="another_valid",
            check="models.Q(value__in=[1, 2, 3])",
            replace=False,
        )
    )
    assert modefied_tree.code == result


def test_fix_replace():
    result = """
class TestClass(Token):
    class Meta:
        constraints = [
            models.CheckConstraint(name="value_valid", check=models.Q(value__in=[1, 2, 3]))
        ]
    """

    source_tree = cst.parse_module(SOURCE)
    modefied_tree = source_tree.visit(
        gen_fix_for_choices_constraint(
            "TestClass",
            name="value_valid",
            check="models.Q(value__in=[1, 2, 3])",
            replace=True,
        )
    )
    assert modefied_tree.code == result


def test_fix_meta_add_constraints():
    source = """
class TestClass(Token):
    class Meta:
        db_table = 'test_class'
    """
    result = """
class TestClass(Token):
    class Meta:
        db_table = 'test_class'
        constraints = [models.CheckConstraint(name="value_valid", check=models.Q(value__in=[1, 2, 3]))]
    """

    source_tree = cst.parse_module(source)
    modefied_tree = source_tree.visit(
        gen_fix_for_choices_constraint(
            "TestClass",
            name="value_valid",
            check="models.Q(value__in=[1, 2, 3])",
            replace=False,
        )
    )
    assert modefied_tree.code == result
