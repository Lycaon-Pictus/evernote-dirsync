#!/usr/bin/env python

import sys
import os
import hashlib
import binascii




import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors




def get_auth_token():
    return open(auth_file_path).read().strip()

def get_sync_notebook_id():
    notebooks = note_store.listNotebooks(auth_token)
    names = [n.name for n in notebooks]
    try:
        idx = names.index(sync_notebook_name)
        return notebooks[idx].guid
    except ValueError:
        print "There is no notebook named '" + sync_notebook_name + "'"
        exit(1)

def get_note_count():
    count_obj = note_store.findNoteCounts(auth_token, filter, False).notebookCounts
    if count_obj is None or not notebook_id in count_obj:
        return 0
    return count_obj[notebook_id]

def get_sync_file_list():
    cloud_files = get_cloud_files()
    local_file_path = [f
                       for f in map(lambda x:local_dir_path + "/" + x,
                                    os.listdir(local_dir_path))
                       if
                       os.path.isfile(f) and
                       os.path.splitext(f)[1] == file_extension and
                       os.path.basename(f) not in cloud_files]
    return local_file_path

def create_new_note(file_path, mime):
    # import pdb; pdb.set_trace()
    file_name = os.path.basename(file_path)
    file_cont = open(file_path, "rb").read()
    md5 = hashlib.md5()
    md5.update(file_cont)
    hash = md5.digest()
    
    data = Types.Data()
    data.size = len(file_cont)
    data.bodyHash = hash
    data.body = file_cont

    attr = Types.ResourceAttributes()
    attr.fileName = file_name

    resource = Types.Resource()
    resource.mime = mime
    resource.data = data
    resource.attributes = attr

    note = Types.Note()
    note.title = file_name
    note.resources = [resource]
    note.notebookGuid = notebook_id
    note.content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>
<ul>
<li></li>
</ul>
<hr/>
<en-media type="%(mime)s" hash="%(hash)s" />
</en-note>""" % {"mime":mime, "hash":binascii.hexlify(hash)}
    note_store.createNote(auth_token, note)

def get_note_store():
    user_store_uri         = "https://" + evernote_host + "/edam/user"
    user_store_http_client = THttpClient.THttpClient(user_store_uri)
    user_store_protoclo    = TBinaryProtocol.TBinaryProtocol(user_store_http_client)
    user_store             = UserStore.Client(user_store_protoclo)

    note_store_url         = user_store.getNoteStoreUrl(auth_token)
    note_store_http_client = THttpClient.THttpClient(note_store_url)
    note_store_protocol    = TBinaryProtocol.TBinaryProtocol(note_store_http_client)
    return NoteStore.Client(note_store_protocol)
    
def get_cloud_files():
    check_note_num = 100
    filter = NoteStore.NoteFilter(notebookGuid=notebook_id)
    temp_list = note_store.findNotes(auth_token,
                                     filter,
                                     0,
                                     check_note_num)
    ret = [x.title for x in temp_list.notes]
    all_note_count = temp_list.totalNotes
    ever_got_count = len(temp_list.notes)
    while ever_got_count < all_note_count:
        temp_list = note_store.findNotes(auth_token,
                                         filter,
                                         ever_got_count,
                                         check_note_num)
        ret += [x.title for x in temp_list.notes]
        ever_got_count += len(temp_list.notes)
    return ret

def upload_files():
    file_path = get_sync_file_list()
    for f in file_path:
        print f
        create_new_note(f, mime_type)



file_extension = ".pdf"
mime_type      = "application/pdf"

auth_file_path     = "temp/.devtoken.prod"
evernote_host      = "www.evernote.com"
local_dir_path     = "temp/files"
sync_notebook_name = "reading list"



auth_token     = get_auth_token()
note_store     = get_note_store()
notebook_id    = get_sync_notebook_id()



upload_files()
