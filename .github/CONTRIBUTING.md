# Contributing

Anyone is very welcome to contribute to this package :)

## Instructions

- Clone repository
- Run `make install`
- Implement your updates
- Run `make test`
- Create a Pull Request

## Building and releasing your package

Building a new version of the application contains steps:

- Bump the version of your package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`.
- Create a `GitHub release`.
- And... publish 🙂 `poetry publish --build`
