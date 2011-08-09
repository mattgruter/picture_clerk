"""
Created on 2011/08/09

@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2011 Matthias Grueter
@license: GPL
"""
import repo
import config


class RepoFactory(object):
    """
    Repo factory methods
    """

    @staticmethod
    def init_dir(connector):
        """
        Initialize the repository directory and return a Repo instance
        
        @param connector: connector to the directory to be initialized
        @type connecor: connetor.Connector
        @return: the initialize Repo instance
        @rtype: repo.Repo
        """
        try:
            connector.connect()
            r = repo.Repo(connector, pic_dir=config.PIC_DIR,
                          config_file=config.CONFIG_FILE)
            r.init_repo()
        except:
            connector.disconnect()
            raise
        
        return r


    @staticmethod
    def create_and_init_dir(connector):
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
        
        return RepoFactory.init_dir(connector)
                