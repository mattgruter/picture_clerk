"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import repo
import config
import copy


class RepoFactory(object):
    """
    Repo factory methods
    """

    @staticmethod
    def init_dir(connector,
                 pic_dir=config.PIC_DIR, config_file=config.CONFIG_FILE):
        """
        Initialize the repository directory and return a Repo instance
        
        @param connector: connector to the directory to be initialized
        @type connecor: connetor.Connector
        @return: the initialize Repo instance
        @rtype: repo.Repo
        """
        try:
            connector.connect()
            r = repo.Repo(connector, pic_dir, config_file)
            r.init_repo()
        except:
            connector.disconnect()
            raise
        
        return r


    @staticmethod
    def create_and_init_dir(connector, pic_dir=config.PIC_DIR,
                            config_file=config.CONFIG_FILE):
        """
        Create the repository directory and return an initialized Repo instance
        
        @param connector: connector to the dir to be created and initialized
        @type connector: connector.Connector
        @return: the initialize Repo instance
        @rtype: repo.Repo
        """
        try:
            connector.connect()
            connector.mkdir('.')
        except:
            connector.disconnect()
            raise
        
        return RepoFactory.init_dir(connector, pic_dir, config_file)
                
    @staticmethod
    def clone_repo(src_repo, dest_connector):
        """
        Clone an existing directory at a new location
        
        @param src_repo: the repository to be cloned
        @type src_repo: repo.Repo
        @param dest_connector: connector pointing to the location of the new
                               clone-repo
        @type dest_connector: connector.Connector
        @return: the clone-repo instance
        @rtype: repo.Repo
        """
        src_repo.connect()
        src_repo.load_index()
        src_repo.disconnect()
        
        dest_repo = RepoFactory.create_and_init_dir(dest_connector,
                                                    src_repo.pic_dir,
                                                    src_repo.config_file)
        
        dest_repo.index = copy.deepcopy(src_repo.index)
        dest_repo.config = copy.copy(src_repo.config)
        
        for picture in src_repo.index:
            for fname in picture.get_filenames():
                src_repo.connector.copy(fname, dest_connector, dest=fname)
                
        return dest_repo
        