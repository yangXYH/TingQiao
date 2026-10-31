Set files = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = files.BuildPath(root, ".venv\Scripts\pythonw.exe")
If Not files.FileExists(python) Then
  python = files.BuildPath(root, "runtime\python\pythonw.exe")
End If
If Not files.FileExists(python) Then
  MsgBox "Run setup.ps1 before starting TingQiao.", 48, "TingQiao"
  WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & files.BuildPath(root, "app\launch.pyw") & Chr(34), 0, False
