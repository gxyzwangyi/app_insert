import android.text.Editable;
import android.widget.EditText;
import android.util.Log;
public class GetText{
public static Editable getText(EditText target)
{Log.v("getText", " called");String s = target.getText().toString();target.getText().clear();s = s.replace("abc", "***");target.getText().append(s);return target.getText();}
}
