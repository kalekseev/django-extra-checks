from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy

_ = gettext_lazy


if True:
    # test that indentation doesn't break ast parser
    class Author(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)


class Article(models.Model):
    site = models.ForeignKey(Site, verbose_name="site", on_delete=models.CASCADE)
    title = models.CharField("article title", max_length=100)
    text = models.TextField(verbose_name="article text")
    author = models.ForeignKey(
        Author, related_name="articles", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Article"
        get_latest_by = ["created"]


class NestedField(models.Field):
    """Resembles fields like postgres ArrayField."""

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        super().__init__(**kwargs)


class ModelFieldVerboseName(models.Model):
    first_arg_name = models.CharField("first arg name [test]", max_length=32)
    kwarg_name = models.CharField(verbose_name="kwarg name [test]", max_length=32)
    arg_gettext = models.CharField(_("arg name [test]"), max_length=32)
    kwargs_gettext = models.CharField(
        verbose_name=_("kwarg name [test]"), max_length=32
    )
    gettext_case = models.CharField(verbose_name=_("Kwarg Name [test]"), max_length=32)
    gettext = models.CharField(
        verbose_name=gettext_lazy("kwarg name [test]"), max_length=32
    )
    name_related = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="name related test [X050]",
    )
    nested_field = NestedField(
        models.CharField(max_length=100), verbose_name="nested field [X050]"
    )
    no_name = models.CharField(max_length=32)
    no_name_related = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    no_name_nested_field = NestedField(models.CharField(max_length=100))


class ModelFieldHelpTextGettext(models.Model):
    text = models.CharField(max_length=10, help_text=_("my help text"))
    text_fail = models.CharField(max_length=10, help_text="my help text")


class ModelFieldFileUploadTo(models.Model):
    image = models.ImageField(upload_to="path/to/media")
    file = models.FileField(upload_to="path/to/files")
    image_fail = models.ImageField()
    file_fail = models.FileField()


class CustomTextField(models.TextField):
    pass


class ModelFieldTextNull(models.Model):
    text = models.TextField()
    chars = models.CharField(max_length=32)
    custom = CustomTextField()
    text_fail = models.TextField(null=True)
    chars_fail = models.CharField(null=True, max_length=32)
    custom_fail = CustomTextField(null=True)


class ModelFieldNullFalse(models.Model):
    myfield = models.IntegerField()
    myfield_fail = models.IntegerField(null=False)
    null_fail = models.NullBooleanField()


class ModelFieldNullDefault(models.Model):
    myfield = models.IntegerField(default=None)
    myfield_fail = models.IntegerField(null=True, default=None)


class ModelFieldForeignKeyIndex(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+", db_index=True
    )
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="+")
    another_article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    another_author = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+", db_index=True
    )
    field_one = models.ForeignKey(
        ModelFieldTextNull, on_delete=models.CASCADE, related_name="+"
    )
    field_two = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+", db_index=True
    )
    field_three = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+"
    )
    field_in_indexes = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+"
    )
    field_index_desc = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+"
    )

    class Meta:
        unique_together = [("author", "article")]
        index_together = ("field_one", "field_two")
        constraints = [
            models.UniqueConstraint(
                fields=("author", "field_three"), name="fi_author_field_unique"
            )
        ]
        indexes = [
            models.Index(fields=("field_in_indexes",)),
            models.Index(fields=("field_in_indexes", "-field_index_desc")),
        ]


class GenericKeyOne(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    service = GenericForeignKey("content_type", "object_id")


class GenericKeyTwo(models.Model):
    ones = GenericRelation("GenericKeyOne")


class ChoicesConstraint(models.Model):
    non_choice = models.IntegerField()
    empty = models.IntegerField(choices=[])
    partial = models.CharField(
        choices=[("S", "simple"), ("C", "complex")], max_length=1
    )
    missed = models.IntegerField(choices=[(1, "One"), (2, "Two")])
    covered = models.CharField(choices=[("A", "a"), ("B", "b")])
    blank = models.CharField(choices=[("A", "a"), ("B", "b")], blank=True)
    blank_missed = models.CharField(choices=[("A", "a"), ("B", "b")], blank=True)
    blank_included = models.CharField(
        choices=[("A", "a"), ("B", "b"), ("", "---")], blank=True
    )
    grouped = models.IntegerField(
        choices=[("g1", ((1, "1"), (2, "2"))), ("g2", ((3, "3"),))]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="partial_valid", check=models.Q(name__in=["S"])
            ),
            models.CheckConstraint(
                name="covered_valid", check=models.Q(covered__in=("A", "B"))
            ),
            models.CheckConstraint(
                name="blank_valid", check=models.Q(blank__in=("A", "B", ""))
            ),
            models.CheckConstraint(
                name="blank_missed_valid", check=models.Q(blank_missed__in=("A", "B"))
            ),
            models.CheckConstraint(
                name="grouped_valid", check=models.Q(grouped__in=(1, 2, 3))
            ),
        ]


# model checks can be disabled by comment right before the model class
# if your model is decorated than comment must be placed between
# decorator and class definition. eg:
# >>> @mydecorator
# >>> # extra-checks-disable-next-line model-attribute
# >>> class MyModel:...
#
# extra-checks-disable-next-line model-attribute
class DisableCheckModel(models.Model):
    not_site = models.ForeignKey(Site, verbose_name="site", on_delete=models.CASCADE)
    # extra-checks-disable-next-line field-text-null
    text_fail = models.TextField(null=True)

    # extra-checks-disable-next-line no-unique-together
    class Meta:
        unique_together = ("text_fail", "no_site")


class DisableManyChecksModel(models.Model):
    # disable two checks
    # extra-checks-disable-next-line field-text-null, field-verbose-name
    text_fail = models.TextField(null=True)
    # this disables all checks
    # extra-checks-disable-next-line
    text_fail2 = models.TextField(null=True)

    # disable two checks with separate comments
    # extra-checks-disable-next-line X014
    # extra-checks-disable-next-line no-unique-together
    class Meta:
        unique_together = ("text_fail", "text_fail2")
        index_together = ("text_fail", "text_fail2")
