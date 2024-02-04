# End-To-End Timing Analysis

The repository is used to reproduce the evaluation from

*Timing Analysis of Cause-Effect Chains with Heterogeneous Communication Mechanisms*

for RTNS 2023.

https://dl.acm.org/doi/abs/10.1145/3575757.3593640

## Environment Setup
### Requirements

To run the experiments Python 3 is required (Python 3.10+ should work). Moreover, the following packages are required:

Please install Python 3 and the required packages.


### File Structure

    .
    ├── output                       # Placeholder for outputs (generated during runtime)
    │   ├── step1                    # Single ECU chains + results
    │   ├── step2                    # Interconnected ECU chains + result
    |   └── step3                    # Plots as in the paper
    ├── e2e                          # Placeholder for the evaluation
    │   ├── cechains                 # Cause-effect chains
    │   ├── tasks   # Tasks and tasksets
    │   ├── __main__.py              # Main file for the evaluation
    │   ├── analysis.py              # Analysis
    │   ├── benchmark_WATERS.py      # The benchmark of our analysis
    │   ├── helpers.py               # Help functions that are used for the evaluation
    │   └── plot.py                  # Generating plots
    └── README.md

The experiments in the main function are divided into 3 steps:
1. Generating tasks and chains
2. Analysis of the chains
3. Plotting the results

In each step, the machines loads the results from the previous step, conducts the step described above, and saves the results in the corresponding folder in output.  


## How to run the experiments

To run the experiments, use
```
python3.10 e2e -p1 -n10 -s0
```

The script takes 3 inputs:
- p: number of processors that should be used in parallel for the computation
- n: number of tasksets that should be generated
- s: steps that should be conducted
    - 1: only step 1
    - 2: only step 2
    - 3: only step 3
    - 0: all 3 steps one after the other.


### Authors

* Mario Günzel
* Niklas Ueter
* Kuan-Hsun Chen
* Jian-Jia Chen


### Acknowledgments

This work has been supported by Deutsche Forschungsgemeinschaft (DFG), as part of Sus-Aware (Project No. 398602212). This result is part of a project (PropRT) that has received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation programme (grant agreement No. 865170).


### License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details