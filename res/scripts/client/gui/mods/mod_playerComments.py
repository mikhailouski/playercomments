import BigWorld # pyright: ignore[reportMissingImports]
import json
import os
from gui import SystemMessages, DialogsInterface
from gui.Scaleform.framework.managers.context_menu import AbstractContextMenuHandler # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.meta.SimpleDialogMeta import SimpleDialogMeta # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.dialogs import DIALOG_BUTTON_ID as BTN_ID # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.lobby.user_cm_handlers import BaseUserCMHandler # pyright: ignore[reportMissingImports]

MOD_NAME = 'Player Comments Mod'
MOD_VERSION = '{{VERSION}}'

comments_path = 'res_mods/configs/mod_playerComments.json'
comments = {}

def load_comments():
    global comments
    try:
        if os.path.exists(comments_path):
            with open(comments_path, 'r') as f:
                comments = json.load(f)
            print('[%s] Loaded %d comments' % (MOD_NAME, len(comments)))
    except Exception as e:
        print('[%s] Load error: %s' % (MOD_NAME, e))
        comments = {}

def save_comments():
    try:
        if not os.path.exists(os.path.dirname(comments_path)):
            os.makedirs(os.path.dirname(comments_path))
        with open(comments_path, 'w') as f:
            json.dump(comments, f, indent=2)
        print('[%s] Saved %d comments' % (MOD_NAME, len(comments)))
    except Exception as e:
        print('[%s] Save error: %s' % (MOD_NAME, e))

original_generate_options = BaseUserCMHandler._generateOptions

def patched_generate_options(self, ctx=None):
    options = original_generate_options(self, ctx)
    if not hasattr(self, '_ctx'):
        print('[%s] Skipping patch for %s - no _ctx' % (MOD_NAME, self.__class__.__name__))
        return options
    options.append(self._makeSeparator())
    comment_btn_id = 'PLAYER_COMMENT'
    db_id = get_db_id_from_ctx(self._ctx)
    db_id_str = str(db_id) if db_id is not None else ''
    label = u'Изменить комментарий' if db_id_str in comments else u'Оставить комментарий'
    enabled = db_id is not None
    options.append(self._makeItem(comment_btn_id, label, {
        'enabled': enabled,
        'iconType': 'info'
    }))
    return options

BaseUserCMHandler._generateOptions = patched_generate_options

original_init = BaseUserCMHandler.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if hasattr(self, '_handlers'):
        self._handlers['PLAYER_COMMENT'] = 'onPlayerComment'
    else:
        print('[%s] Warning: No _handlers in %s init' % (MOD_NAME, self.__class__.__name__))

BaseUserCMHandler.__init__ = patched_init

def get_db_id_from_ctx(ctx):
    db_id = None
    try:
        if hasattr(ctx, 'HasMember') and ctx.HasMember('dbID'):
            member = ctx.GetMember('dbID')
            if hasattr(member, 'GetNumber'):
                db_id = member.GetNumber()
        elif hasattr(ctx, 'get'):
            db_id = ctx.get('dbID') or ctx.get('accountDBID') or ctx.get('databaseID')
        elif hasattr(ctx, '__getitem__'):
            db_id = ctx['dbID'] if 'dbID' in ctx else None
        else:
            db_id = getattr(ctx, 'dbID', None)
    except Exception as e:
        print('[%s] Error accessing dbID from ctx: %s' % (MOD_NAME, e))
    print('[%s] Extracted db_id: %s (ctx type: %s)' % (MOD_NAME, db_id, type(ctx)))
    return db_id

def on_player_comment(self):
    if not hasattr(self, '_ctx'):
        print('[%s] Skipping on_player_comment for %s - no _ctx' % (MOD_NAME, self.__class__.__name__))
        return
    print('[%s] Context type: %s (class: %s)' % (MOD_NAME, type(self._ctx), self.__class__.__name__))
    db_id = get_db_id_from_ctx(self._ctx)
    if db_id is None:
        SystemMessages.pushMessage('Ошибка: ID игрока не найден', SystemMessages.SM_TYPE.ErrorHeader)
        print('[%s] No dbID in ctx' % MOD_NAME)
        return
    db_id_str = str(db_id)
    initial_value = comments.get(db_id_str, u'')

    def callback(result):
        if result[0] == BTN_ID.SUBMIT and result[1].strip():
            comments[db_id_str] = result[1].strip()
            save_comments()
            SystemMessages.pushMessage(u'Комментарий сохранён!', SystemMessages.SM_TYPE.InformationHeader)
        elif result[0] == BTN_ID.CANCEL:
            pass

    meta = SimpleDialogMeta(
        header=u'Комментарий к игроку',
        message=u'Введите текст (макс. 200 символов):',
        initialValue=initial_value[:200],
        inputType=SimpleDialogMeta.INPUT_TYPE.ALPHANUMERIC,
        buttons=[BTN_ID.CANCEL, BTN_ID.SUBMIT]
    )
    DialogsInterface.showDialog(meta, callback)

BaseUserCMHandler.onPlayerComment = on_player_comment

def init():
    load_comments()
    print('[%s] Mod initialized' % MOD_NAME)

def fini():
    save_comments()
    print('[%s] Mod finalized' % MOD_NAME)