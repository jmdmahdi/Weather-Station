package ir.jmdmahdi.weatherstation.ui.main;

import androidx.arch.core.util.Function;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Transformations;
import androidx.lifecycle.ViewModel;

import java.util.Date;

public class LogViewModel extends ViewModel {

    private MutableLiveData<Integer> mIndex = new MutableLiveData<>();
    private MutableLiveData<String> mText = new MutableLiveData<>();

    public void setIndex(int index) {
        mIndex.setValue(index);
    }

    public void appendText(String text) {
        String currentDateTimeString = java.text.DateFormat.getDateTimeInstance().format(new Date());
        String val = mText.getValue();
        if (val != null)
            mText.setValue(val + "\n" + currentDateTimeString + "> " + text);
        else
            mText.setValue(currentDateTimeString + "> " + text);
    }

    public LiveData<String> getText() {
        return mText;
    }
}