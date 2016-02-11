import sqlite3

INSERT, UPDATE, DELETE  = 1, 2, 3

def syncLayer(layer):
    filename, layername = layer.source().split("|")
    layername = layername.split("=")[-1]
    con = sqlite3.connect(filename)
    cursor = con.cursor()
    cursor.execute("SELECT repository_uri FROM geogig_metadata;")
    url = cursor.fetchone()[0]
    local = {c[0]:c for c in localChanges(cursor, layername)}
    remote = {c[0]:c for c in remoteChanges(cursor, url, layername)}
    conflicts = {}
    for fid in local:
        if fid in remote:
            conflicts[fid] = (local[fid], remote[fid])
    if conflicts:
        solved = solveConflicts(conflicts)
        if solved is None:
            return
        remote.update(solved)

    #TODO apply changes in "remote" dict onto geopackage table

    commitid = getRepoRemoteHeadCommitId(url, layername)
    cursor.execute("UPDATE geogig_audited_tables SET root_tree_id='%s' WHERE table_name='%s'" % (commitid, layername))
    
    changes = localChanges(cursor, layername)
    #TODO push changes

    layer.reload()
    layer.triggerRepaint()

def localChanges(cursor, layername):
    cursor.execute("SELECT * FROM %s_audit;" % layername)
    changes = cursor.fetchall()
    return changes


def remoteChanges(cursor, url, layername):
    cursor.execute("SELECT root_tree_id FROM geogig_audited_tables WHERE table_name='%s';" % layername)
    commitid = cursor.fetchone()[0]
    #TODO fetch changes with url, layername, commitid

def getRepoRemoteHeadCommitId(url, layername):
    #TODO
    pass


def solveConflicts(conflicts):
    #TODO
    return True
