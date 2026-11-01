"""Small Python 3.12 demonstrations; no claim to execute other languages."""
from abc import ABC, abstractmethod
from typing import ClassVar


def examples():
    class Speaker:
        def speak(self):
            return 'base'

    class Child(Speaker):
        def speak(self):
            return 'child'

    class Duck:
        def speak(self):
            return 'duck'

    def hear(value):
        return value.speak()

    class Parent:
        shared: ClassVar[list[str]] = []

        def __init__(self):
            self.local = []
            self.__value = 7

    left, right = Parent(), Parent()
    left.shared.append('shared')
    left.local.append('local')
    shared_before_shadow = list(right.shared)
    left.shared = ['shadow']

    def annotated(value: int) -> int:
        return value

    class Overwritten:
        def f(self, value):
            return value

        def f(self, first, second):  # noqa: F811 - intentional language example
            return first + second

    class Required(ABC):
        @abstractmethod
        def run(self):
            return 'base implementation'

    class Complete(Required):
        def run(self):
            return super().run() + ' then concrete'

    def error_name(operation):
        try:
            operation()
        except (TypeError, AttributeError) as error:
            return type(error).__name__
        return None

    class Root:
        pass

    class First(Root):
        pass

    class Second(Root):
        pass

    class Diamond(First, Second):
        pass

    return {
        'override': hear(Child()), 'duck_without_inheritance': hear(Duck()),
        'class_attribute_shared': shared_before_shadow,
        'instance_attribute_separate': list(right.local),
        'shadow_does_not_replace_class_attribute': list(Parent.shared),
        'mangled_name_accessible': left._Parent__value,
        'annotation_not_enforced': annotated('text'),
        'incompatible_addition': error_name(lambda: 1 + '1'),
        'last_definition_replaces_first': error_name(lambda: Overwritten().f(1)),
        'last_definition_works': Overwritten().f(1, 2),
        'abstract_instantiation': error_name(Required),
        'concrete_calls_abstract_body': Complete().run(),
        'mro': [item.__name__ for item in Diamond.__mro__],
    }


if __name__ == '__main__':
    import json
    print(json.dumps(examples(), indent=2))
