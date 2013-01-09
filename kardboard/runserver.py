import sys
from kardboard.app import app
from kardboard import auth, forms, models, tasks, tickethelpers, util, version, views
import logging


def profile_run():
    from werkzeug import run_simple
    from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream
    print "* Profiling"
    f = open('./profiler.log', 'w')
    profiled_app = ProfilerMiddleware(app, MergeStream(sys.stderr, f))
    run_simple('localhost', 5000, profiled_app,
        use_reloader=True, use_debugger=True)


def run():
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True, use_reloader=True, host= '0.0.0.0')

if __name__ == "__main__":
    if "profile" in sys.argv:
        profile_run()
    else:
        run()
