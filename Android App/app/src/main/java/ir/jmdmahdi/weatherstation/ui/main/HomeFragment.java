package ir.jmdmahdi.weatherstation.ui.main;

import android.animation.ObjectAnimator;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.graphics.drawable.RotateDrawable;
import android.os.Build;
import android.os.Bundle;
import android.text.format.DateFormat;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.LinearInterpolator;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.Nullable;
import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProviders;

import java.util.Calendar;
import java.util.Locale;

import ir.jmdmahdi.weatherstation.R;

/**
 * A placeholder fragment containing a simple view.
 */
public class HomeFragment extends Fragment {

    private static final String ARG_SECTION_NUMBER = "section_number";
    private HomeViewModel pageViewModel;

    public static HomeFragment newInstance(int index) {
        HomeFragment fragment = new HomeFragment();
        Bundle bundle = new Bundle();
        bundle.putInt(ARG_SECTION_NUMBER, index);
        fragment.setArguments(bundle);
        return fragment;
    }

    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    public void updateHome(float[] data) {
        pageViewModel.setTemperature(data[2]);
        pageViewModel.setPressure(data[3] / 100);
        pageViewModel.setLightIntensity(data[4]);
        pageViewModel.setHumidity(data[5]);
        pageViewModel.setWindSpeed(data[6]);
        pageViewModel.setWindAngle(data[7]);
        pageViewModel.setTimeStamp(System.currentTimeMillis() / 1000);

    }

    public void updateConnectionStatus(boolean status) {
        pageViewModel.setConnected(status);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        pageViewModel = ViewModelProviders.of(this).get(HomeViewModel.class);
        int index = 1;
        if (getArguments() != null) {
            index = getArguments().getInt(ARG_SECTION_NUMBER);
        }
        pageViewModel.setIndex(index);
        pageViewModel.setTemperature((float) 0);
        pageViewModel.setPressure((float) 0);
        pageViewModel.setLightIntensity((float) 0);
        pageViewModel.setHumidity((float) 0);
        pageViewModel.setWindSpeed((float) 0);
        pageViewModel.setWindAngle((float) 0);
        pageViewModel.setTimeStamp(0);
        pageViewModel.setConnected(false);
    }

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState) {
        View root = inflater.inflate(R.layout.fragment_main, container, false);
        final TextView textViewDate = root.findViewById(R.id.textViewDate);
        final TextView textViewTime = root.findViewById(R.id.textViewTime);
        pageViewModel.getTimeStamp().observe(this, new Observer<Long>() {
            @Override
            public void onChanged(@Nullable Long timestamp) {
                Calendar cal = Calendar.getInstance(Locale.ENGLISH);
                cal.setTimeInMillis(timestamp * 1000);
                String date = DateFormat.format("d MMMM yyyy", cal).toString();
                String time = DateFormat.format("HH:mm:ss", cal).toString();
                textViewDate.setText(date);
                textViewTime.setText(time);
            }
        });

        final TextView textViewAngle = root.findViewById(R.id.textViewAngle);
        final ImageView compassNeedle = root.findViewById(R.id.compassNeedle);
        pageViewModel.getWindAngle().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float angle) {
                compassNeedle.setRotation(angle);
                textViewAngle.setText(String.format("%s °", angle));
            }
        });

        final TextView textViewSpeed = root.findViewById(R.id.textViewSpeed);
        pageViewModel.getWindSpeed().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float speed) {
                textViewSpeed.setText(String.format("%s m/s", speed));
            }
        });

        final TextView textViewTemprature = root.findViewById(R.id.textViewTemprature);
        pageViewModel.getTemperature().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float temp) {
                textViewTemprature.setText(String.format("%s °C", temp));
            }
        });

        final TextView textViewLigthIntensity = root.findViewById(R.id.textViewLigthIntensity);
        pageViewModel.getLightIntensity().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float lightintensity) {
                textViewLigthIntensity.setText(String.format("%s LUX", lightintensity));
            }
        });

        final TextView textViewHumdity = root.findViewById(R.id.textViewHumdity);
        pageViewModel.getHumidity().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float humidty) {
                textViewHumdity.setText(String.format("%s %%", humidty));
            }
        });

        final TextView textViewPressure = root.findViewById(R.id.textViewPressure);
        pageViewModel.getPressure().observe(this, new Observer<Float>() {
            @Override
            public void onChanged(Float presuure) {
                textViewPressure.setText(String.format("%s hPa", presuure));
            }
        });

        final TextView textViewStatus = root.findViewById(R.id.textViewStatus);
        pageViewModel.getConnected().observe(this, new Observer<Boolean>() {
            @Override
            public void onChanged(Boolean connectStatus) {
                if (connectStatus) {
                    textViewStatus.setText("Connected");
                    textViewStatus.setTextColor(Color.GREEN);
                } else {
                    textViewStatus.setText("Disconnected");
                    textViewStatus.setTextColor(Color.RED);
                }
            }
        });

        return root;
    }
}