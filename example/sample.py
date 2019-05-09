from inspect import Parameter, signature
import io
import os
import pickle
import sys


class Missile:
    def __init__(self, name):
        self.name = name
        self._sio_out = io.StringIO()
        self._sio_err = io.StringIO()

    def load_and_launch(self, f, *args, **kwargs):
        # Grab arguments as a dict
        args_l = list(args)
        args_dict = {}
        for k, p in signature(f).parameters.items():
            if p.kind in [
                    Parameter.POSITIONAL_OR_KEYWORD,
                    Parameter.POSITIONAL_ONLY,
                    Parameter.KEYWORD_ONLY]:
                if p.default is Parameter.empty:
                    args_dict[k] = args_l.pop(0)
                else:
                    args_dict[k] = p.default
            elif p.kind == Parameter.VAR_POSITIONAL:
                args_dict[k] = args_l
                del args_l
            elif p.kind == Parameter.VAR_KEYWORD:
                args_dict = dict(args_dict, **kwargs)

        self._args_dict = args_dict
        # Redirect stdout/err to StringIO
        sys.stdout = self._sio_out
        sys.stderr = self._sio_err

        self._ret = f(*args, **kwargs)

        self._sio_out.seek(0)
        self._sio_err.seek(0)

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        self.launch()

    def launch(self):
        self.stdout()
        self.stderr()
        self.args()
        self.ret()


class S3Missile(Missile):
    def __init__(**conf):
        pass

    def stdout(self):
        pass

    def stderr(self):
        pass

    def args(self):
        pass

    def ret(self):
        pass


class LocalMissile(Missile):
    def __init__(self, name, **conf):
        super(LocalMissile, self).__init__(name)

        self.outdir = os.path.join(self.name, 'outputs')
        os.makedirs(self.outdir, exist_ok=True)

    def stdout(self):
        with open(os.path.join(self.outdir, 'stdout.txt'), 'w') as f:
            f.write(self._sio_out.read())

    def stderr(self):
        with open(os.path.join(self.outdir, 'stderr.txt'), 'w') as f:
            f.write(self._sio_err.read())

    def args(self):
        with open(os.path.join(self.outdir, 'args.pkl'), 'wb') as f:
            pickle.dump(self._args_dict, f)

    def ret(self):
        with open(os.path.join(self.outdir, 'return.pkl'), 'wb') as f:
            pickle.dump(self._ret, f)


def nikita(name):
    missile = LocalMissile(name)

    def wrapper(func):
        def _wrapper(*args, **kwargs):
            return missile.load_and_launch(func, *args, **kwargs)

        return _wrapper

    return wrapper


@nikita('sample_experiment')
def run(a, *args, b=2, **kwargs):
    print(a, b)
    print('a + b = %i' % (a + b))
    return a, b, a + b


if __name__ == '__main__':
    ret = run(1, 'hoge', 'fuga', b=3, foo='bar')
