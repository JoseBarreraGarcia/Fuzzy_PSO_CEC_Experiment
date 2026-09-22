# ===== console_logging.py =====
import os
from colorama import Fore, init
init(autoreset=True)

def _prefix():
    wid = os.environ.get('PSO_WORKER_ID')
    return f"[W{wid}] " if wid is not None else ""

def _is_summary_only():
    return os.environ.get('PSO_CONSOLE_SUMMARY') == '1'

def print_initial(tag: str, best_initial: float):
    if _is_summary_only():
        return
    p = _prefix()
    print(f"{p}{tag} - Initial Best Fitness: {best_initial:.2e}")
    print(f"{p}{'-' * 102}")

def print_iteration(it: int, max_it: int, best: float, opt: float,
                    dt: float, xpt: float, xpl: float, div_t: float,
                    print_every_quarter: bool = True):
    if _is_summary_only():
        return

    if max_it <= 0:
        should_print = True
    else:
        step = max(1, max_it // 4) if print_every_quarter else 1
        should_print = (it % step == 0) or (it == max_it)

    if should_print:
        p = _prefix()
        msg = (
            f"{p}Iteration: {it:<4} | "
            f"Best Fitness: {best:>7.2e} | "
            f"Optimum: {opt:>9.2e} | "
            f"Time (s): {dt:>4.3f} | "
            f"XPT: {xpt:>6.2f} | "
            f"XPL: {xpl:>6.2f} | "
            f"DIV: {div_t:>5.2f}"
        )
        print(msg)

def print_final(best_final: float, t_start: float, t_end: float):
    p = _prefix()
    if _is_summary_only():
        # Modo resumen: solo una línea con resultado final
        print(f"{p}{Fore.GREEN}Fitness: {best_final:.2e} | Time: {(t_end - t_start):.2f}s")
        return
    print(f"{p}{'-' * 102}")
    print(f"{p}{Fore.GREEN}Execution time (s): {(t_end - t_start):.2f}")
    print(f"{p}{Fore.GREEN}Best Fitness: {best_final:.2e}")
    print(f"{p}{'-' * 102}")
