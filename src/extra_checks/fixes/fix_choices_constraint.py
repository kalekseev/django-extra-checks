import libcst as cst
from libcst import matchers as m


def gen_fix_for_choices_constraint(
    class_name: str, name: str, check: str, replace: bool = False
) -> m.MatcherDecoratableTransformer:
    class Fixes(m.MatcherDecoratableTransformer):
        def __init__(self) -> None:
            self.is_constraint_updated = False
            super().__init__()

        @m.call_if_inside(m.ClassDef(m.Name(class_name)))
        @m.leave(m.ClassDef(m.Name("Meta")))
        def leave_meta(
            self, node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            if not self.is_constraint_updated and not replace:
                exp = cst.parse_statement(
                    f'constraints = [models.CheckConstraint(name="{name}", check={check})]'
                )
                lines = updated_node.body.body
                return updated_node.with_deep_changes(
                    updated_node.body, body=[*lines, exp]
                )
            self.is_constraint_updated = False
            return updated_node

        if replace:

            @m.call_if_inside(m.ClassDef(m.Name(class_name)))
            @m.call_if_inside(m.ClassDef(m.Name("Meta")))
            @m.call_if_inside(
                m.Assign(targets=[m.AssignTarget(target=m.Name("constraints"))])
            )
            @m.leave(
                m.Call(
                    func=m.Attribute(attr=m.Name("CheckConstraint"))
                    | m.Name("CheckConstraint")
                )
            )
            def fix_existing(self, node: cst.Call, updated_node: cst.Call) -> cst.Call:
                # TODO select either models.CheckConstraint or CheckConstraint
                if node.args[0].value.raw_value == name:
                    return cst.parse_expression(
                        f'models.CheckConstraint(name="{name}", check={check})'
                    )
                return updated_node

        else:

            @m.call_if_inside(m.ClassDef(m.Name(class_name)))
            @m.call_if_inside(m.ClassDef(m.Name("Meta")))
            @m.leave(m.Assign(targets=[m.AssignTarget(target=m.Name("constraints"))]))
            def add_new(self, node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
                self.is_constraint_updated = True
                exp = cst.parse_expression(
                    f'[models.CheckConstraint(name="{name}", check={check})]'
                )
                constraints = updated_node.value.elements
                return updated_node.with_deep_changes(
                    updated_node.value, elements=[*constraints, exp.elements[0]]
                )

    return Fixes()
