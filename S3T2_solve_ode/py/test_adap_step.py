import pytest
import numpy as np
import matplotlib.pyplot as plt

from utils.ode_collection import Harmonic, HarmExp
from utils.utils import get_log_error
from S3T2_solve_ode.py.solve_ode import adaptive_step_integration, AdaptType
from S3T2_solve_ode.py.one_step_methods import (
    ExplicitEulerMethod,
    RungeKuttaMethod,
    EmbeddedRungeKuttaMethod,
)
import S3T2_solve_ode.py.coeffs_collection as collection


@pytest.mark.parametrize('f,y0', (
        (Harmonic(np.array([1., 1.]), 1, 1), np.array([1., 1.])),
        (HarmExp(), np.exp([1, 0])),
))
def test_adaptive(f, y0):
    """
    test adaptive step algorithms
    """
    t0, t1 = 0, 4*np.pi

    atol = 1e-6
    rtol = 1e-3

    tss = []
    yss = []

    methods = (
        (ExplicitEulerMethod(), AdaptType.RUNGE),
        (RungeKuttaMethod(coeffs=collection.rk4_coeffs),            AdaptType.RUNGE),
        (EmbeddedRungeKuttaMethod(coeffs=collection.dopri_coeffs),  AdaptType.EMBEDDED),
    )

    for method, adapt_type in methods:
        f.clear_call_counter()
        ts, ys = adaptive_step_integration(method=method,
                                           func=f, y_start=y0, t_span=(t0, t1),
                                           adapt_type=adapt_type,
                                           atol=atol, rtol=rtol)
        print(f'{method.name} took {f.get_call_counter()} function calls')

        tss.append(np.array(ts))
        yss.append(ys)

    ts = np.array(sorted([t for ts in tss for t in ts]))
    exact = f[ts].T
    y0 = np.array([y[0] for y in exact])

    # plots
    plt.figure('y(t)'), plt.suptitle('test_adaptive: y(t)'), plt.xlabel('t'), plt.ylabel('y')
    plt.plot(ts, y0, 'ko-', label='exact')

    plt.figure('dt(t)'), plt.suptitle('test_adaptive: step sizes'), plt.xlabel('t'), plt.ylabel('dt')
    plt.figure('dy(t)'), plt.suptitle('test_adaptive: accuracies'), plt.xlabel('t'), plt.ylabel('accuracy')

    for (m, _), ts, ys in zip(methods, tss, yss):
        plt.figure('y(t)'), plt.plot(ts, [y[0] for y in ys], '.', label=m.name)
        plt.figure('dt(t)'), plt.plot(ts[:-1], ts[1:] - ts[:-1], '.-', label=m.name)
        plt.figure('dy(t)'), plt.plot(ts, get_log_error(f[ts].T, ys), '.-', label=m.name)

    plt.figure('y(t)'), plt.legend()
    plt.figure('dt(t)'), plt.legend()
    plt.figure('dy(t)'), plt.legend()

    plt.show()


def test_adaptive_order():
    """
    test adaptive algorithms convergence
    """
    t0, t1 = 0, 2*np.pi
    y0 = np.array([1., 1.])
    f = Harmonic(y0, 1, 1)

    methods = (
        (ExplicitEulerMethod(),                                     AdaptType.RUNGE),
        (RungeKuttaMethod(coeffs=collection.rk4_coeffs),            AdaptType.RUNGE),
        (EmbeddedRungeKuttaMethod(coeffs=collection.dopri_coeffs),  AdaptType.EMBEDDED),
    )
    tols = 10. ** -np.arange(3, 9)

    plt.figure()
    for i, (method, adapt_type) in enumerate(methods):
        print(method.name)
        fcs = []
        errs = []
        for tol in tols:
            f.clear_call_counter()
            ts, ys = adaptive_step_integration(method=method,
                                               func=f, y_start=y0, t_span=(t0, t1),
                                               adapt_type=adapt_type,
                                               atol=tol, rtol=tol*1e3)
            err = np.linalg.norm(ys[-1] - f[t1])
            fc = f.get_call_counter()
            print(f'{method.name}: {fc} RHS calls, err = {err:.5f}')
            errs.append(err)
            fcs.append(fc)

        x = np.log10(fcs)
        y = -np.log10(errs)
        k, b = np.polyfit(x, y, 1)
        plt.plot(x, k*x+b, 'k:')
        plt.plot(x, y, 'p', label=f'{method.name} ({k:.2f})')
    plt.suptitle('test_adaptive_order: check RHS evals')
    plt.xlabel('log10(function_calls)')
    plt.ylabel('accuracy')
    plt.legend()
    plt.show()
