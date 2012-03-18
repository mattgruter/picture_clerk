"""
@author: Matthias Grueter <matthias@grueter.name>
@copyright: Copyright (c) 2012 Matthias Grueter
@license: GPL

"""
import time

from dulwich.repo import Repo
from dulwich.objects import Blob, Tree, Commit

from file_store import FileStore
from file_store import FileAlreadyOpenError, FileNotOpenError


# FIXME: base GitFileStore on PlainFileStore


class GitFileStore(FileStore):
    def __init__(self, path):
        FileStore.__init__(self, path)

    def open(self, mode, revision=None):
        if not self.opened:
            if not revision:
                self._fh = open(self.path, mode)
                self.opened = True
            else:
    #            return git.retrieve(path, revision)
                raise NotImplementedError
        else:
            raise FileAlreadyOpenError

    def commit(self):
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

        if self.opened:
            blob = Blob.from_raw_chunks(Blob.type_num, self._fh.readlines())
        else:
            raise FileNotOpenError

        # FIXME: get mode from physical file
        mode = 0100644

        head = self.repo.refs['refs/heads/' + self.branch]
#        head = self.repo.head()
        prev_commit = self.repo[head]
        tree = self.repo[prev_commit.tree]

        tree[self.path] = (mode, blob.id)

        # populate Git commit object
        commit = Commit()
        commit.tree = tree.id
        commit.parents = [head]
        commit.author = commit.committer = self.author
        commit.commit_time = commit.author_time = int(time.time())
        commit.commit_timezone = commit.author_timezone = 0
        commit.encoding = "UTF-8"

        # FIXME: create useful commit message
        commit.message = "Committing %s" % self.path

        self.repo.object_store.add_object(blob)
        self.repo.object_store.add_object(tree)
        self.repo.object_store.add_object(commit)
        self.repo.refs['refs/heads/' + self.branch] = commit.id
#        self.repo.refs['HEAD'] = commit.id

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None
            self.opened = False
        else:
            raise FileNotOpenError

    def rollback(self):
#        git.revert_hard(path)
        raise NotImplementedError

    def get_log(self, path, limit):
#        git.log(path, limit)
        raise NotImplementedError

