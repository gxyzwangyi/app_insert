import android.util.Log;
import java.net.URL;
public class MyUrl{
public static java.net.URL URL(String url)
{Log.v("ctor method called", " URL");try {return new java.net.URL(url);} catch(Exception e) {return null;}}
}
