# Define the neural network model
import torch.nn as nn
from .config import input_axes, output_axes, pdms_only


class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()

        self.flatten = nn.Flatten()
        if pdms_only:
            # 12,226,254,85,81,104,28,4
            self.linear_relu_stack = nn.Sequential(
                nn.Linear(len(input_axes), 226),  # Input layer
                nn.ReLU(),
                nn.Linear(226, 254),
                nn.ReLU(),
                nn.Linear(254, 85),
                nn.ReLU(),
                nn.Linear(85, 81),
                nn.ReLU(),
                nn.Linear(81, 104),
                nn.ReLU(),
                nn.Linear(104, 28),
                nn.ReLU(),
                nn.Linear(28, len(output_axes)),
            )
        else:
            self.linear_relu_stack = nn.Sequential(
                nn.Linear(len(input_axes), 411),  # Input layer
                nn.ReLU(),
                nn.Linear(411, 299),
                nn.ReLU(),
                nn.Linear(299, 119),
                nn.ReLU(),
                nn.Linear(119, 58),
                nn.ReLU(),
                nn.Linear(58, 35),
                nn.ReLU(),
                nn.Linear(35, len(output_axes)),
            )

        # self.linear_relu_stack = nn.Sequential(
        #     nn.Linear(len(input_axes), 72),  # Input layer
        #     nn.ReLU(),
        #     nn.Linear(72, 34),
        #     nn.ReLU(),
        #     nn.Linear(34, 23),
        #     # nn.ReLU(),
        #     # nn.Linear(64, 64),
        #     # nn.Dropout(p=0.2),
        #     # nn.ReLU(),
        #     nn.ReLU(),
        #     nn.Linear(23, len(output_axes)),
        # )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits
