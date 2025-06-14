# Define the neural network model
import torch.nn as nn
from .config import input_axes, output_axes


class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()

        self.flatten = nn.Flatten()
        # self.linear_relu_stack = nn.Sequential(
        #     nn.Linear(len(input_axes), 256),  # Input layer with 4 features
        #     nn.ReLU(),
        #     nn.Linear(256, 256),
        #     nn.ReLU(),
        #     nn.Linear(256, 64),
        #     nn.ReLU(),
        #     # nn.Dropout(p=0.2),
        #     # nn.ReLU(),
        #     nn.Linear(64, 8),
        #     nn.ReLU(),
        #     nn.Linear(8, len(output_axes)),
        # )

        self.linear_relu_stack = nn.Sequential(
            nn.Linear(len(input_axes), 256),  # Input layer with 4 features
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            # nn.Dropout(p=0.2),
            # nn.ReLU(),
            nn.ReLU(),
            nn.Linear(64, len(output_axes)),
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits
