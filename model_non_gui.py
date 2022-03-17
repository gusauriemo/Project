import nengo
import nengo_spa as spa
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.io import loadmat
from nengo.dists import Choice
import itertools
from nengo.utils.ensemble import response_curves, tuning_curves
import scipy.io


data_path = "/Users/gustavo/Documents/Final Year Project/POLY3/UMAPiano-DB-Poly-3-A.mat"
full_path = "/Users/gustavo/Documents/Final Year Project/POLY3/full_poly3-A-Eb-C.mat"
data_path2 = "/Users/gustavo/Documents/Final Year Project/POLY3/UMAPiano-DB-Poly-3-Eb.mat"
LabelA= "/Users/gustavo/Documents/Final Year Project/POLY3/Poly_3_A_noteLabels.mat"
labelEb= "/Users/gustavo/Documents/Final Year Project/POLY3/Poly_3_Eb_noteLabels.mat"
labels = "/Users/gustavo/Documents/Final Year Project/POLY3/labels_poly3-A-Eb-C.mat"
matrix_data = loadmat(full_path)
matrix_data2 = loadmat(data_path2)
label_data = loadmat(labels)
label_data2= loadmat(labelEb)

nn= 30 #number of notes used
nn2 = 3828
initial = 0
final = initial+nn
period=0.15

input_array = (np.log10(matrix_data["matrix"]))
#print(np.max(input_array))
input_array[input_array<0] = 0
input_array2 = (np.log10(matrix_data2["matrix"]))
input_array2[input_array2<0] = 0
output_array = (label_data["labels"])*3
#print(np.sum(output_array))
output_array2 = (label_data2["labels"])

D = nn #number of dimensions
N = D*50 #smallest number of neurons per ensemble

simulation_runtime = 200


with nengo.Network(seed=0) as net:
    #Correct signal - i.e., desired output
    correct_stim = nengo.Node(nengo.processes.PresentInput(output_array[:, initial:final], presentation_time=0.15))
    correct_ensemble = nengo.Ensemble(N*4, D, radius=4)

    #Input signal — hearing
    hearing_stim = nengo.Node(nengo.processes.PresentInput(input_array[:, initial:final], presentation_time=0.15))
    hearing_ensemble = nengo.Ensemble(N*4, D, radius=4, seed=0)
    decision_ensemble = nengo.Ensemble(N*5, D, radius=4, seed=0)


    # Connections
    nengo.Connection(correct_stim, correct_ensemble[:D])
    nengo.Connection(hearing_stim, hearing_ensemble[:D])
    #nengo.Connection(hearing_ensemble[:D], hearing_ensemble[D:], synapse=0.2)
    
    learn_conn = nengo.Connection(hearing_ensemble, decision_ensemble,  #can also use zero in the array instead of np.random.random(1)
        learning_rule_type = nengo.PES(learning_rate=8e-5)
        )

    error = nengo.Ensemble(N*5, D, radius = 4)

    #Learning connections
    nengo.Connection(correct_ensemble, error, transform=-1)
    nengo.Connection(decision_ensemble, error, transform=1)
    nengo.Connection(error, learn_conn.learning_rule)


    # -- inhibit errors after 40 seconds
    #inhib = nengo.Node(lambda t: 2.0 if t > 60.0 else 0.0)
    #nengo.Connection(inhib, error.neurons, transform=[[-1]] * error.n_neurons)

    #Probes

    probe1 = nengo.Probe(correct_ensemble, "decoded_output", synapse=0.01)
    probe2 = nengo.Probe(hearing_ensemble, "decoded_output", synapse=0.01)
    probe3 = nengo.Probe(error, synapse=0.01)
    probe4 = nengo.Probe(decision_ensemble, "decoded_output", synapse=0.01)
    probe_weights = nengo.Probe(learn_conn, "weights", synapse=0.01, sample_every= simulation_runtime) #obtains weights at the end of the simulation

#with net:
    # Direct neurons to ensemble connection
    #conn2 = nengo.Connection(ens1.neurons, ens2, transform=decoders)

with nengo.Simulator(net) as sim:
    sim.run(simulation_runtime)

decoders = (sim.data[probe_weights])

scipy.io.savemat('decoder200_2.mat', mdict={'decoders': decoders})

#once the simulation is over, we can use these decoders to simply run the simlation directly (no learning) and evaluate the loss for both training and testing


# Plot the input signals and decoded ensemble values

plt.figure()
plt.plot(sim.trange(), sim.data[probe1], c= "k", label="c")
plt.plot(sim.trange(), sim.data[probe4], c= "r",label="b")
plt.figure()
plt.plot(sim.trange(), sim.data[probe3], c= "b",label="b")

#plt.legend(loc="best")

# Find weight row with max variance
#plt.figure()
#neuron = np.argmax(np.mean(np.var(sim.data[probe_weights], axis=0), axis=1))
#plt.plot(sim.trange(sample_every=simulation_runtime), sim.data[probe_weights][..., neuron])
#plt.ylabel("Connection weight")

plt.show()