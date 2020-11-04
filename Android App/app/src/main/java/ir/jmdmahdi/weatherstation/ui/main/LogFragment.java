package ir.jmdmahdi.weatherstation.ui.main;

import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.widget.CompoundButton;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.arch.core.util.Function;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.Transformations;
import androidx.lifecycle.ViewModelProviders;

import ir.jmdmahdi.weatherstation.R;

/**
 * A placeholder fragment containing a simple view.
 */
public class LogFragment extends Fragment {

    private static final String ARG_SECTION_NUMBER = "section_number";
    private ScrollView mScrollView;
    private TextView textView;
    private Switch autoScroll;
    private Boolean autoScrollStatus = true;
    private LogViewModel pageViewModel;

    public static LogFragment newInstance(int index) {
        LogFragment fragment = new LogFragment();
        Bundle bundle = new Bundle();
        bundle.putInt(ARG_SECTION_NUMBER, index);
        fragment.setArguments(bundle);
        return fragment;
    }

    public void insertLog(String text) {
        pageViewModel.appendText(text);
        if (autoScrollStatus)
            mScrollView.post(new Runnable() {
                public void run() {
                    mScrollView.fullScroll(View.FOCUS_DOWN);
                }
            });
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        pageViewModel = ViewModelProviders.of(this).get(LogViewModel.class);
        int index = 1;
        if (getArguments() != null) {
            index = getArguments().getInt(ARG_SECTION_NUMBER);
        }
        pageViewModel.setIndex(index);
    }

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState) {
        View root = inflater.inflate(R.layout.fragment_log, container, false);
        textView = root.findViewById(R.id.logtext);
        pageViewModel.getText().observe(this, new Observer<String>() {
            @Override
            public void onChanged(@Nullable String s) {
                textView.setText(s);
            }
        });
        mScrollView = root.findViewById(R.id.scrollable);
        autoScroll = root.findViewById(R.id.autoScroll);
        autoScroll.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                autoScrollStatus = isChecked;
            }
        });
        return root;
    }
}