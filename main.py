import torch
from ae import Autoencoder
from ae import TaskNetwork
import matplotlib.pyplot as plt


class AutoencoderPipeline:

    def __init__(self):
        self.control_sequence_size = 32
        self.latent_size = 3
        self.encoder_layer_sizes = [15]
        self.decoder_layer_sizes = [15]
        self.autoencoder = Autoencoder(self.control_sequence_size, self.latent_size, self.encoder_layer_sizes, self.decoder_layer_sizes)
        self.task_network = TaskNetwork(self.latent_size)


    def acquire_new_data(self, last_control_seq, N=10, perturbation_strength=0.05):
        """
        Acquire new data for training the autoencoder.

        Returns:
        - The new control sequence with the lowest autoencoder objective function value after sampling.
        """
        lowest_loss = float('inf')
        best_seq = None

        for _ in range(N):
            # Perturb the control sequence by a random vector
            perturbation = (torch.rand_like(last_control_seq)-0.5) * perturbation_strength
            perturbed_seq = torch.clamp(last_control_seq + perturbation, min=0, max=1)

            # Evaluate the perturbed sequence without updating the autoencoder weights
            _, loss = self.autoencoder.evaluate(perturbed_seq.unsqueeze(0))

            if loss < lowest_loss:
                lowest_loss = loss
                best_seq = perturbed_seq

        return best_seq
    

    def train_model_pipeline_combined(self, control_seq):
        self.autoencoder.train()
        self.task_network.train()
        
        ae_loss = 0
        latent = self.autoencoder.encode(control_seq)
        
        # Forward pass through the task network
        task_pred = self.task_network(latent)
        # Example task objective: minimize the difference from a target value
        target_value = torch.tensor([desired_value], device=control_seq.device)
        task_loss = (task_pred - target_value).pow(2)
        
        # Combine losses
        combined_loss = ae_loss + task_loss
        
        # Zero the gradients
        self.autoencoder.optimizer.zero_grad()
        self.task_optimizer.zero_grad()
        
        # Backward pass
        combined_loss.backward()
        
        # Update weights
        self.autoencoder.optimizer.step()
        self.task_optimizer.step()

        return combined_loss.item()
    
    
    def train_model_pipeline(self, epochs):
        losses = []
        new_control_seq_values = []
        new_control_seq = torch.rand(self.control_sequence_size)
        print(new_control_seq)
        for i in range(epochs):
            new_control_seq = self.acquire_new_data(new_control_seq, 100, 2)
            loss = self.autoencoder.train_model(new_control_seq.unsqueeze(0))
            losses.append(loss)
            new_control_seq_values.append(new_control_seq.tolist()) 
        
        print(new_control_seq)
        print(losses[-1])

        # Plotting losses
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)  # First subplot for the losses
        plt.plot(range(1, epochs + 1), losses, label="Training Loss")
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Model Loss Over Time')
        plt.legend()

        # Plotting values of new_control_seq over time
        plt.subplot(1, 2, 2)  # Second subplot for the new_control_seq values
        new_control_seq_values = list(zip(*new_control_seq_values))
        for seq_index, seq_values in enumerate(new_control_seq_values):
            plt.plot(range(1, epochs + 1), seq_values, label=f"Seq {seq_index + 1}")
        plt.xlabel('Epoch')
        plt.ylabel('Value')
        plt.title('New Control Seq Values Over Time')
        plt.show()
        


# Binary cross entropy loss for binary inputs
# Sigmoid Acctivation in decoder output

if __name__ == "__main__":
    aep = AutoencoderPipeline()
    epochs = 100

    aep.train_model_pipeline(epochs)
