import sys
import os
from cluster import categorize_victims, cluster_victims, export_category_data

## importa classes
from vs.environment import Env
from explorer import Explorer
from rescuer import Rescuer

def main(data_folder_name):
   
    # Set the path to config files and data files for the environment
    current_folder = os.path.abspath(os.getcwd())
    data_folder = os.path.abspath(os.path.join(current_folder, data_folder_name))

    # Instantiate the environment
    env = Env(data_folder)
    
    # config files for the agents
    rescuer_file = os.path.join(data_folder, "rescuer_config.txt")
    explorer_file = os.path.join(data_folder, "explorer_config.txt")
    
    # Instantiate agents rescuer and explorer
    resc = Rescuer(env, rescuer_file)

    # Explorer needs to know rescuer to send the map
    # that's why rescuer is instantiated before
    exp = Explorer(env, explorer_file, resc)

    # Run the environment simulator
    env.run()

    # Get victims from rescuer
    victims = resc.victims

    # Categorize and cluster victims
    categorized_victims = categorize_victims(victims)
    clustered_victims = cluster_victims(categorized_victims)

    # Export cluster data to CSV
    output_folder = 'output'
    export_category_data(clustered_victims, output_folder)
    
        
if __name__ == '__main__':
    """ To get data from a different folder than the default called data
    pass it by the argument line"""
    
    if len(sys.argv) > 1:
        data_folder_name = sys.argv[1]
    else:
        data_folder_name = os.path.join("datasets", "data_10v_12x12")
        
    main(data_folder_name)