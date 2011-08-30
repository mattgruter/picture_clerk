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
    def init_dir(connector, create_dir=False, repo_config=None, repo_index=None):
        """
        Initialize the repository directory and return a Repo instance
        
        @param connector: connector to the directory to be initialized
        @type connector: connetor.Connector
        @param create_dir: set True if repo dir should be created (default False)
        @type create_dir: bool
        @return: the initialize Repo instance
        @rtype: repo.Repo
        """
        try:
            connector.connect()

            # create repo dir (optional)
            if create_dir:
                connector.mkdir('.')

            # create necessary directories
            connector.mkdir(config.PIC_DIR)
            
            # create Repo instance
            r = repo.Repo()
            
            if repo_config:
                r.config = repo_config
            else:
                # create default config and write it to file
                r.create_default_config()
            
            if repo_index:
                r.index = repo_index
            
            #with connector.open(config_file, 'wb') as config_fh:    
            config_fh = connector.open(config.CONFIG_FILE, 'wb')
            try:
                r.write_config(config_fh)
            finally:
                config_fh.close()
            
            #with connector.open(config.INDEX_FILE, 'wb') as index_fh:
            index_fh = connector.open(config.INDEX_FILE, 'wb')
            try:
                r.write_index(index_fh)
            finally:
                index_fh.close()
            
        except:
            connector.disconnect()
            raise
       
        return r
    
                
    @staticmethod
    def clone_repo(src_repo, src_connector, dest_connector):
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
        
        try:
            src_connector.connect()
            
            #with connector.open(config_file, 'rb') as config_fh:    
            config_fh = src_connector.open(config.CONFIG_FILE, 'rb')
            try:
                src_repo.load_config(config_fh)
            finally:
                config_fh.close()
             
            #with connector.open(index_file, 'rb') as config_fh:    
            index_fh = src_connector.open(config.INDEX_FILE, 'rb')
            try:
                src_repo.load_config(index_fh)
            finally:
                config_fh.close()
        
            dest_config = copy.copy(src_repo.config)
            dest_index = copy.deepcopy(src_repo.index)
            dest_repo = RepoFactory.init_dir(dest_connector,
                                             create_dir=True,
                                             repo_config=dest_config,
                                             repo_index=dest_index)
            
            for picture in src_repo.index:
                for fname in picture.get_filenames():
                    src_repo.connector.copy(fname, dest_connector, dest=fname)
                    
        finally:   
            src_connector.disconnect()
                
        return dest_repo
        