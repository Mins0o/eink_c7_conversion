import numpy as np
import matplotlib.pyplot as plt
import sys

def plot_curves(strengths):
    """
    Plots blue multiplier curves for a list of strengths on a single graph.
    """
    plt.figure(figsize=(10, 6))

    for strength in strengths:
        if strength <= 0:
            print(f"Skipping invalid strength value: {strength}")
            continue

        # x-axis: blue_ratio from 0 to 1.
        blue_ratio = np.linspace(0, 3, 100)
        
        # y-axis: The multiplier for the blue channel
        # Sigmoid formula: A normalized logistic function
        k = float(strength)
        
        # def f(x, k_val):
        #     ret = 3 * np.sin(x * np.pi) * np.sin(x * np.pi) * np.exp(-3*x)
        #     return ret

        # def g(x):
        #     ret = (-2*np.pi**2*np.sin(np.pi*x)**2 - 9*np.sin(np.pi*x)**2 - 6*np.pi*np.sin(np.pi*x)*np.cos(np.pi*x) - 2*np.pi**2*np.cos(np.pi*x)**2)/(27*np.exp(3*x) + 12*np.pi**2*np.exp(3*x))
        #     return ret

        def normalized(x):
            ret = g(x) - g(0)
            ret = ret / (g(1) - g(0))
            return ret

        def clone_norm(x,k_val):
            x=x*1.5 # 1.5 to shorten the curve
            return ((1/4)*(-4*np.pi**2*np.exp(3*x) + 6*np.pi*np.sin(2*np.pi*x) - 9*np.cos(2*np.pi*x) + 9 + 4*np.pi**2)*np.exp(3 - 3*x)/(np.pi**2*(1 - np.exp(3))) - 1)*k_val+1


        #plt.plot(blue_ratio, f(blue_ratio,k), label=f'Strength = {strength}')
        #plt.plot(blue_ratio, normalized(blue_ratio), label=f'Strength = {strength} (g)', linestyle='--')
        plt.plot(blue_ratio, clone_norm(blue_ratio, k), label=f'Strength = {strength}', linestyle=':')

    plt.title('Blue Reduction Effect (Sigmoid Curve)')
    plt.xlabel('Original Blue Ratio (Blue / (R+G+B))')
    plt.ylabel('Blue Channel Multiplier (New Blue / Old Blue)')
    plt.grid(True)
    plt.legend()
    plt.xlim(0, 3)
    plt.ylim(0, 1.5)
    plt.axhline(y=1, color='r', linestyle='--', label='No Change')
    
    output_filename = "blue_reduction_effect.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

    


if __name__ == "__main__":
    if len(sys.argv) > 1:
        strength_values = []
        for arg in sys.argv[1:]:
            try:
                strength_val = float(arg)
                strength_values.append(strength_val)
            except ValueError:
                print(f"Warning: Skipping invalid number '{arg}'")
        
        if strength_values:
            plot_curves(strength_values)
        else:
            print("No valid strength values provided.")
    else:
        print("Usage: python plot_blue_reduction_effect.py <strength1> [strength2] ...")
        print("Example: python plot_blue_reduction_effect.py 5 10 15")


    import sympy as sp
    import numpy as np # lambdify will use numpy functions

    # --- Define Symbols and Simplified Expression ---
    x = sp.symbols('x')
    pi = sp.pi
    exp = sp.exp
    sin = sp.sin
    cos = sp.cos

    # This is the simplified normalized_x from the previous step
    normalized_x_expr = (1/4)*(-4*pi**2*exp(3*x) + 6*pi*sin(2*pi*x) - 9*cos(2*pi*x) + 9 + 4*pi**2)*exp(3 - 3*x)/(pi**2*(1 - exp(3)))

    # --- Create the Callable Function ---
    # Convert the symbolic expression into a numerical function
    # This function is now ready to be used as a boundary condition
    normalized_bc = sp.lambdify(x, normalized_x_expr, 'numpy')

    # --- Test the Function ---
    # You can now call it like any other Python function
    value_at_0_5 = normalized_bc(0.5)
    #print(f"The value of the function at x = 0.5 is: {value_at_0_5}")

    # You can also pass NumPy arrays
    x_vals = np.linspace(0, 1, 5)
    bc_values = normalized_bc(x_vals)
    #print(f"\nValues for x = {x_vals}:")
    #print(bc_values)

