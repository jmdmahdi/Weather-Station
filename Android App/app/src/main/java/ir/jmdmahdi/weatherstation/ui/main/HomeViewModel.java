package ir.jmdmahdi.weatherstation.ui.main;

import androidx.arch.core.util.Function;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Transformations;
import androidx.lifecycle.ViewModel;

public class HomeViewModel extends ViewModel {

    private MutableLiveData<Integer> mIndex = new MutableLiveData<>();
    private MutableLiveData<Float> Humidity = new MutableLiveData<>();
    private MutableLiveData<Long> TimeStamp = new MutableLiveData<>();
    private MutableLiveData<Float> Temperature = new MutableLiveData<>();
    private MutableLiveData<Float> LightIntensity = new MutableLiveData<>();
    private MutableLiveData<Float> Pressure = new MutableLiveData<>();
    private MutableLiveData<Float> WindSpeed = new MutableLiveData<>();
    private MutableLiveData<Float> WindAngle = new MutableLiveData<>();
    private MutableLiveData<Boolean> Connected = new MutableLiveData<>();

    public void setIndex(int index) {
        mIndex.setValue(index);
    }

    public void setConnected(boolean status) {
        Connected.setValue(status);
    }

    public void setTimeStamp(long _TimeStamp) {
        TimeStamp.setValue(_TimeStamp);
    }

    public void setHumidity(Float _Humidity) {
        Humidity.setValue(_Humidity);
    }

    public void setTemperature(Float _Temperature) {
        Temperature.setValue(_Temperature);
    }

    public void setLightIntensity(Float _LightIntensity) {
        LightIntensity.setValue(_LightIntensity);
    }

    public void setPressure(Float _Pressure) {
        Pressure.setValue(_Pressure);
    }

    public void setWindSpeed(Float _WindSpeed) {
        WindSpeed.setValue(_WindSpeed);
    }

    public void setWindAngle(Float _WindAngle) {
        WindAngle.setValue(_WindAngle);
    }

    public MutableLiveData<Long> getTimeStamp() {
        return TimeStamp;
    }

    public MutableLiveData<Boolean> getConnected() {
        return Connected;
    }

    public MutableLiveData<Float> getHumidity() {
        return Humidity;
    }

    public MutableLiveData<Float> getTemperature() {
        return Temperature;
    }

    public MutableLiveData<Float> getLightIntensity() {
        return LightIntensity;
    }

    public MutableLiveData<Float> getPressure() {
        return Pressure;
    }

    public MutableLiveData<Float> getWindSpeed() {
        return WindSpeed;
    }

    public MutableLiveData<Float> getWindAngle() {
        return WindAngle;
    }
}