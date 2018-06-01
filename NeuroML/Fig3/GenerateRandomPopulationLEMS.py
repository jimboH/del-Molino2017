
import os
import numpy as np
import random
from neuroml import (NeuroMLDocument, Network, Population, ContinuousConnectionInstanceW, ContinuousProjection,
                     ExplicitInput, SilentSynapse, PulseGenerator)
import neuroml.writers as writers
from pyneuroml.lems.LEMSSimulation import LEMSSimulation


# This script generates a new xml file that describes the connection between the different network population

def generatePopulationLEMS(pops, n_pop, amplitudes, baseline):
    def generatePopulationProjection(from_pop, to_pop, n_from_pop, n_to_pop, w_to_from_pop, p_to_from_pop, net):
        connection_count = 0
        projection = ContinuousProjection(id='%s_%s' %(from_pop, to_pop),
                                          presynaptic_population='%sPop' %from_pop,
                                          postsynaptic_population='%sPop' %to_pop)
        net.continuous_projections.append(projection)
        for idx_from_pop in range(n_from_pop):
            for idx_to_pop in range(n_to_pop):
                if random.random() <= p_to_from_pop:
                    connection = ContinuousConnectionInstanceW(id=connection_count,
                                                               pre_cell='../%sPop[%i]' %(from_pop, idx_from_pop),
                                                               post_cell='../%sPop[%i]' %(to_pop, idx_to_pop),
                                                               pre_component='silent1',
                                                               post_component='rs',
                                                               weight=w_to_from_pop /(p_to_from_pop * n_from_pop))
                    projection.continuous_connection_instance_ws.append(connection)
                    connection_count += 1


    # Connection probabilities for each pop in the population
    w_to_from_pops = np.array([[2.42, -.033, -0.80,     0],
                               [2.97, -3.45,  2.13,     0],
                               [4.64,     0,     0, -2.79],
                               [0.71,     0, -0.16,     0]])
    p_to_from_pop = np.array([[0.02, 1,    1,     0],
                              [0.01, 1, 0.85,     0],
                              [0.01, 0,    0,  0.55],
                              [0.01, 0,  0.5,     0]])

    nml_doc = NeuroMLDocument(id='RandomPopulation')

    # Add silent synapsis
    silent_syn = SilentSynapse(id='silent1')
    nml_doc.silent_synapses.append(silent_syn)

    for pop_idx, pop in enumerate(pops):
        pulse = PulseGenerator(id='baseline_%s' %pop, delay='0ms', duration='300ms', amplitude=amplitudes[pop_idx])
        nml_doc.pulse_generators.append(pulse)

        if pop == 'vip':
            pulse_mod = PulseGenerator(id='modVIP', delay='100ms', duration='200ms', amplitude='10 pA')
            nml_doc.pulse_generators.append(pulse_mod)

    # Create the network and add the 4 different populations
    net = Network(id='net2')
    nml_doc.networks.append(net)

    # Populate the network with the 4 populations
    for pop_idx, pop in enumerate(pops):
        pop = Population(id='%sPop' %pop, component=(pops[pop_idx]).upper(), size=n_pop[pop_idx])
        net.populations.append(pop)

    for from_idx, from_pop in enumerate(pops):
        for to_idx, to_pop in enumerate(pops):
            generatePopulationProjection(pops[from_idx], pops[to_idx], n_pop[from_idx], n_pop[to_idx],
                                         w_to_from_pops[to_idx, from_idx], p_to_from_pop[to_idx, from_idx], net)
    # Add inputs
    for pop_idx, pop in enumerate(pops):
        for n_idx in range(n_pop[pop_idx]):
            exp_input = ExplicitInput(target='%sPop[%i]' %(pop, n_idx), input='baseline_%s' %pops[pop_idx], destination='synapses')
            net.explicit_inputs.append(exp_input)

            # if vip add modulatory input
            if pop == 'vip':
                mod_input = ExplicitInput(target='vipPop[%i]' %n_idx, input='modVIP', destination='synapses')
                net.explicit_inputs.append(mod_input)

    nml_file = 'RandomPopulationRate_%s_baseline.nml' %baseline
    writers.NeuroMLWriter.write(nml_doc, nml_file)
    print('Written network file to: %s' %nml_file)

    # Validate the NeuroML
    from neuroml.utils import validate_neuroml2
    validate_neuroml2(nml_file)


def generatePopulationSimulationLEMS(n_pops, baseline, pops):
    # Create LEMS file
    sim_id = 'LEMS_PopulationSim%sBaseline.xml' %baseline
    sim_t = 300 # ms
    dt = 0.1
    ls = LEMSSimulation(sim_id, sim_t, dt, 'net2')
    colours = ['#0000ff', '#ff0000', '#DDA0DD', '#00ff00']

    # Add additional LEMS files
    # Add Rate Base Components
    ls.include_lems_file('../RateBased.xml', include_included=True)
    # Add specifications for the Rate Base Components
    ls.include_lems_file('../RateBasedSpecifications_%s_baseline.xml' %baseline, include_included=True)
    # Add the network definition
    ls.include_lems_file('RandomPopulationRate_%s_baseline.nml' %baseline, include_included=True)

    for pop_idx, pop in enumerate(pops):
        disp1 = '%s' %pop
        ls.create_display(disp1, '%s' %pop, -1, 12)
        for n_pop in range(n_pops[pop_idx]):
            ls.add_line_to_display(disp1, '%s%d' % (pop, n_pop)   , '%sPop[%d]/r' % (pop, n_pop),   color=colours[pop_idx])

    for pop_idx, pop in enumerate(pops):
        # Create output file
        of1 = 'of_%s' %pop
        ls.create_output_file(of1, 'Population_%s_%s_baseline.dat' %(pop, baseline) )
        for n_pop in range(n_pops[pop_idx]):
            ls.add_column_to_output_file(of1, 'r_%s_%d' % (pop, n_pop), '%sPop[%d]/r' % (pop, n_pop))

    save_path = os.path.join(sim_id)
    ls.save_to_file(file_name=save_path)

