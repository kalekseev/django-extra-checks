## Change Log

### Unreleased

### 0.12.0

- Update test matrix: Django 3.2-4.1 X python 3.6-3.11
- Remove deprecated `@ignore_checks`
- Remove deprecated `ignore_types`

### 0.11.0

- Remove `default_app_config`.

### 0.10.0

- Add option `skipif` that accepts user function
- Deprecate `ignore_types`

### 0.9.1

- Replace DeprecationWarning with FutureWarning for `@ignore_checks`

### 0.9.0

- Disable checks with `extra-checks-disable-next-line` comment
- Deprecate `@ignore_checks`
- Make ast parsing lazy
- Add global log level

### 0.8.0

- Add checks:
  - `field-choices-constraint`

### 0.7.1

- Fix index checks level and message

### 0.7.0

- Check `field-foreign-key-index` now accepts `when: indexes` instead of `when: unique_toegether` because now it search for duplicate indexes in `Meta.indexes`, `Meta.unique_toegether` and `Meta.constraints`
- Add checks:
  - `no-unique-together`
  - `no-index-together`

### 0.6.0

- Add checks:
  - `field-default-null`

### 0.5.0

- Fix `ignore_checks`
- Skip models fields not inherited from `fields.Field`
- Add `ignore_types` option

### 0.4.1

- Fix message for `field-verbose-name-gettext-case`

### 0.4.0

- Add infra for rest framework serializers checks
- Add checks:
  - `drf-model-serializer-extra-kwargs`
  - `drf-model-serializer-meta-attribute`
  - `model-admin`

### 0.3.0

- Add `include_apps` option.
- Fix ast crashes.

### 0.2.1

- Fix ast parsing of indented block #1

### 0.2.0

- First public release

### 0.1.0

- First alpha
