from typing import List, Dict, Optional, Tuple, Union
from mp_api.client import MPRester
import json

class MPIClient:
    def __init__(self, api_key: str):
        """
        Initialize the MPI client.
        
        Args:
            api_key: Materials Project API key
        """
        self.api_key = api_key
        
    def execute_query(self, query: str) -> List[Dict]:
        """
        Execute a custom query against the Materials Project API.
        
        Args:
            query: JSON string containing query parameters
            
        Returns:
            List of material dictionaries
        """
        try:
            # Parse query parameters
            query_params = json.loads(query)
            
            with MPRester(self.api_key) as mpr:
                # Build search criteria
                criteria = {}
                
                # Handle common query parameters
                if "elements" in query_params:
                    criteria["elements"] = query_params["elements"]
                    
                if "exclude_elements" in query_params:
                    criteria["exclude_elements"] = query_params["exclude_elements"]
                    
                if "energy_above_hull" in query_params:
                    value = query_params["energy_above_hull"]
                    if isinstance(value, dict):
                        if "$gte" in value:
                            criteria["energy_above_hull"] = (value["$gte"], value["$lt"] if "$lt" in value else None)
                    else:
                        min_e, max_e = value
                        criteria["energy_above_hull"] = (min_e, max_e)
                        
                if "num_sites" in query_params:
                    value = query_params["num_sites"]
                    if isinstance(value, dict):
                        if "$gte" in value:
                            criteria["num_sites"] = (value["$gte"], value["$lte"] if "$lte" in value else None)
                    else:
                        min_sites, max_sites = value
                        criteria["num_sites"] = (min_sites, max_sites)
                        
                if "fields" in query_params:
                    criteria["fields"] = query_params["fields"]
                
                # Execute search
                results = mpr.materials.summary.search(**criteria)
                
                # Convert results to list of dictionaries
                materials = []
                for result in results:
                    material = {
                        "material_id": result.material_id,
                        "formula": result.formula_pretty,
                        "elements": [str(elem) for elem in result.elements],
                        "nelements": result.nelements,
                        "nsites": result.nsites,
                        "energy_above_hull": result.energy_above_hull,
                        "energy_per_atom": result.energy_per_atom,
                        "is_stable": result.is_stable,
                        "structure": result.structure.as_dict()
                    }
                    materials.append(material)
                
                return materials
                
        except Exception as e:
            raise RuntimeError(f"Error executing MPI query: {str(e)}") 