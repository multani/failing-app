A set of various applications failing in different ways.

::

    Usage: app.py [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      fail_after       A non web-app which crashes after the...
      flapping_health  /health flaps between OK and not OK at each...
      mem_leak         Leak memory on each /health call
      web_app          A 'normal' web app
