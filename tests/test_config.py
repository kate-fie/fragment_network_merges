import os

from merge.utils import Singleton


class TestConfig(metaclass=Singleton):
    CONFIG_DICT = dict(
        FRAGALYSIS_DATA_DIR="/home/swills/Oxford/data/Fragalysis",
        OUTPUT_DIR="/home/swills/Oxford/fragment_network/fragment_network_merges/data",
        WORKING_DIR=os.path.join(os.getcwd(), "data"),
        N_CPUS_FILTER_PAIR=2,
        # FOR FILTERING THE MERGES POST-DATABASE QUERY
        FILTER_PIPELINE=['DescriptorFilter', 'EmbeddingFilter', 'OverlapFilter'],
        SCORING_PIPELINE=[],  # 'IfpScore'
        FRAGA_VOLUME=0.9,  # the threshold for volume of the merge that comes from fragment A
        COVALENT_RESI='2B',  # for fragmenstein
        ENERGY_THRESHOLD=10,  # embedding filter: ratio of energy of unconstrained vs constrained conformations,
        CLASH_DIST=0.15,  # overlap filter: proportion of ligand overlapping with protein categorized as not fitting,
        COM_RMSD=1,  # fragmenstein filter: threshold for combined RMSD to rule out poses generated by Fragmenstein
        # FOR RUNNING THE ENTIRE PIPELINE
        PIPELINE_DICT={'DescriptorFilter': 'descriptor_filter',
                       'EmbeddingFilter': 'embedding_filter',
                       'ExpansionFilter': 'expansion_filter',
                       'OverlapFilter': 'overlap_filter',
                       'FragmensteinFilter': 'fragmenstein_filter',
                       'IfpScore': 'ifp_score'})

    @classmethod
    def get(cls, key):
        val = os.environ.get(key, None)
        if val:
            return val
        else:
            return cls.CONFIG_DICT[key]

    # this method will allow instances to access config properties as obj.PROPERTY; useful for subclassing
    def __getattr__(self, key):
        if key in self.__dict__:
            val = self.__dict__[key]
            return val
        else:
            return self.get(key)

    def __setattr__(self, key, value):
        if value is not None:
            super(Config_filter, self).__setattr__(key, value)
        # self.CONFIG_DICT[key] = value
        
    def __init__(self):
        pass


config_filter = Config_filter()
