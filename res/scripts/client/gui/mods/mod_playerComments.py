import BigWorld # pyright: ignore[reportMissingImports]
import json
import os
from gui import SystemMessages, DialogsInterface  # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.meta.SimpleDialogMeta import SimpleDialogMeta # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.dialogs import DIALOG_BUTTON_ID as BTN_ID # pyright: ignore[reportMissingImports]
from gui.Scaleform.daapi.view.lobby.user_cm_handlers import BaseUserCMHandler # pyright: ignore[reportMissingImports]

MOD_NAME = 'Player Comments Mod'
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
    db_id_str = str(self._ctx.get('dbID', ''))
    label = u'Изменить комментарий' if db_id_str in comments else u'Оставить комментарий'
    options.append(self._makeItem(comment_btn_id, label, {
        'enabled': True,
        'iconType': 'info'
    }))
    return options

BaseUserCMHandler._generateOptions = patched_generate_options

original_init = BaseUserCMHandler.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if hasattr(self, '_actionHandlers'):
        self._actionHandlers['PLAYER_COMMENT'] = 'onPlayerComment'
    else:
        print('[%s] Warning: No _actionHandlers in %s init' % (MOD_NAME, self.__class__.__name__))

BaseUserCMHandler.__init__ = patched_init

def on_player_comment(self):
    if not hasattr(self, '_ctx'):
        print('[%s] Skipping on_player_comment for %s - no _ctx' % (MOD_NAME, self.__class__.__name__))
        return
    print('[%s] Context: %r (class: %s)' % (MOD_NAME, self._ctx, self.__class__.__name__))
    db_id = self._ctx.get('dbID') or self._ctx.get('accountDBID') or self._ctx.get('databaseID')
    if not db_id:
        SystemMessages.pushMessage('Ошибка: ID игрока не найден', SystemMessages.SM_TYPE.ErrorHeader)
        print('[%s] No dbID in ctx: %r' % (MOD_NAME, self._ctx))
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