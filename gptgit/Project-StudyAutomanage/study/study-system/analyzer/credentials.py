"""Current-user Windows Credential Manager; secrets never enter project files."""
import ctypes
import os
from ctypes import wintypes

TARGET = 'StudyAutomanage/OpenAI/APIKey'


class Credential(ctypes.Structure):
    _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR), ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME), ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR)]


class KeyStore:
    def __init__(self):
        if os.name != 'nt':
            raise OSError('API 키 저장은 Windows 자격 증명 관리자를 사용합니다.')
        self.api = ctypes.WinDLL('Advapi32.dll', use_last_error=True)
        self.api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                      ctypes.POINTER(ctypes.POINTER(Credential))]
        self.api.CredReadW.restype = wintypes.BOOL
        self.api.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
        self.api.CredWriteW.restype = wintypes.BOOL
        self.api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.api.CredDeleteW.restype = wintypes.BOOL
        self.api.CredFree.argtypes = [ctypes.c_void_p]

    def read(self):
        pointer = ctypes.POINTER(Credential)()
        if not self.api.CredReadW(TARGET, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:
                return None
            raise OSError('저장된 API 키에 접근하지 못했습니다.')
        try:
            return ctypes.string_at(pointer.contents.CredentialBlob,
                                    pointer.contents.CredentialBlobSize).decode('utf-8')
        finally:
            self.api.CredFree(pointer)

    def save(self, key):
        if (not isinstance(key, str) or not 12 <= len(key.strip()) <= 2000
                or any(not 33 <= ord(c) <= 126 for c in key.strip())):
            raise ValueError('공백 없는 API 키를 입력하세요.')
        raw = key.strip().encode('utf-8')
        blob = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        credential = Credential(Type=1, TargetName=TARGET, CredentialBlobSize=len(raw),
                                CredentialBlob=blob, Persist=2, UserName='StudyAutomanage')
        try:
            if not self.api.CredWriteW(ctypes.byref(credential), 0):
                raise OSError('API 키를 저장하지 못했습니다.')
        finally:
            ctypes.memset(blob, 0, len(raw))

    def delete(self):
        if not self.api.CredDeleteW(TARGET, 1, 0) and ctypes.get_last_error() != 1168:
            raise OSError('저장된 API 키를 삭제하지 못했습니다.')
