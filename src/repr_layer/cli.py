from ._cli import cli


if __name__ == '__main__':
    from patching import Patch

    with Patch():
        cli()
