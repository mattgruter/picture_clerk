"""git_file_store.py

Git based file store
"""

__author__ = "Matthias Grueter (matthias@grueter.name)"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2011/04/01 $"
__copyright__ = "Copyright (c) 2011 Matthias Grueter"
__license__ = "GPL"


import time
import os.path

# Git support
from dulwich.repo import Repo
from dulwich.objects import Blob, Tree, Commit


from file_store import FileStore


class GitFileStore(FileStore):
    def __init__(self, repo_path, branch, author):
        self.repo = Repo(repo_path)
        self.branch = branch
        self.author = author

    def open(self, path, mode, revision=None):
        if not revision:
            path = os.path.join(self.repo.path, path)
            return open(path, mode)
        else:
#            return git.retrieve(path, revision)
            raise NotImplementedError
            
    def commit(self, path):
        # FIXME: this breaks if git repository just got initialized and no
        #        inital commit has been done before.
        
        # FIXME: the working copy/tree has to be updated as well otherwise the
        #        newly commited file will be out of sync with the working copy
        #        (maybe we have to add the file to the index/stage? check how
        #        RabbitVCS does it.)
        
        # TODO: maybe commit should be a method of the file object so that one
        #       could write:
        #           fh = open("file", 'w')
        #           fh.write("blabla")
        #           fh.close()
        #           fh.commit()
        
        file_path = os.path.join(self.repo.path, path)
        with open(file_path) as f:
            blob = Blob.from_raw_chunks(Blob.type_num, f.readlines())
            
        # FIXME: get mode from physical file
        mode = 0100644
            
        head = self.repo.refs['refs/heads/' + self.branch]
#        head = self.repo.head()
        prev_commit = self.repo[head]
        tree = self.repo[prev_commit.tree]        
            
        tree[path] = (mode, blob.id)

        # populate Git commit object
        commit = Commit()
        commit.tree = tree.id
        commit.parents = [head]
        commit.author = commit.committer = self.author
        commit.commit_time = commit.author_time = int(time.time())
        commit.commit_timezone = commit.author_timezone = 0
        commit.encoding = "UTF-8"
        
        # FIXME: create useful commit message
        commit.message = "Committing %s" % path
        
        self.repo.object_store.add_object(blob)
        self.repo.object_store.add_object(tree)
        self.repo.object_store.add_object(commit)
        self.repo.refs['refs/heads/' + self.branch] = commit.id
#        self.repo.refs['HEAD'] = commit.id
        
    def rollback(self, path):
#        git.revert_hard(path)
        raise NotImplementedError
        
    def get_log(self, path, limit):
#        git.log(path, limit)
        raise NotImplementedError
        
