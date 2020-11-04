package ir.jmdmahdi.weatherstation;

import android.os.Build;
import android.os.Bundle;

import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.snackbar.Snackbar;
import com.google.android.material.tabs.TabLayout;

import androidx.annotation.RequiresApi;
import androidx.fragment.app.Fragment;
import androidx.viewpager.widget.ViewPager;
import androidx.appcompat.app.AppCompatActivity;

import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;

import ir.jmdmahdi.weatherstation.ui.main.LogFragment;
import ir.jmdmahdi.weatherstation.ui.main.SectionsPagerAdapter;

import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.Bundle;

import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.android.material.snackbar.Snackbar;
import com.hoho.android.usbserial.driver.CdcAcmSerialDriver;
import com.hoho.android.usbserial.driver.ProbeTable;
import com.hoho.android.usbserial.driver.UsbSerialDriver;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import com.hoho.android.usbserial.driver.UsbSerialProber;
import com.hoho.android.usbserial.util.SerialInputOutputManager;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;

import android.view.Menu;
import android.view.MenuItem;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity implements SerialInputOutputManager.Listener {
    SectionsPagerAdapter sectionsPagerAdapter;

    private enum UsbPermission {Unknown, Requested, Granted, Denied}

    ;
    private static final String INTENT_ACTION_GRANT_USB = BuildConfig.APPLICATION_ID + ".GRANT_USB";

    private int portNum, baudRate;
    private SerialInputOutputManager usbIoManager;
    private UsbSerialPort usbSerialPort;
    private boolean connected = false;
    private Handler mainLooper;
    private BroadcastReceiver broadcastReceiver;
    private UsbPermission usbPermission = UsbPermission.Unknown;

    private float[] Data = new float[8];

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        sectionsPagerAdapter = new SectionsPagerAdapter(this, getSupportFragmentManager());
        ViewPager viewPager = findViewById(R.id.view_pager);
        viewPager.setAdapter(sectionsPagerAdapter);
        TabLayout tabs = findViewById(R.id.tabs);
        tabs.setupWithViewPager(viewPager);

        broadcastReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (intent.getAction().equals(INTENT_ACTION_GRANT_USB)) {
                    usbPermission = intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)
                            ? UsbPermission.Granted : UsbPermission.Denied;
                    connect();
                }
            }
        };

        mainLooper = new Handler(Looper.getMainLooper());
    }

    @Override
    public void onResume() {
        super.onResume();
        this.registerReceiver(broadcastReceiver, new IntentFilter(INTENT_ACTION_GRANT_USB));

        if (usbPermission == UsbPermission.Unknown || usbPermission == UsbPermission.Granted)
            mainLooper.post(this::connect);
    }

    @Override
    public void onPause() {
        if (connected) {
            Log.d("jmdmahdi:", "disconnected");
            disconnect();
        }
        this.unregisterReceiver(broadcastReceiver);
        super.onPause();
    }

    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    @Override
    public void onNewData(byte[] data) {
        runOnUiThread(() -> {
            sectionsPagerAdapter.updateConnectionStatus(true);
            insertNewData(data);
        });
    }

    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    private void insertNewData(byte[] data) {
        if (data.length != 32) {
            sectionsPagerAdapter.insertLog("Invalid data");
            return;
        }
        Data = new float[8];
        for (int x = 0; x < data.length; x += 4) {
            byte[] bytes = {data[x], data[x + 1], data[x + 2], data[x + 3]};
            Data[x / 4] = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).getFloat();
        }

        sectionsPagerAdapter.insertLog(Data[0] + ", " + Data[1] + ", " + Data[2] + ", " + Data[3] + ", " + Data[4] + ", " + Data[5] + ", " + Data[6] + ", " + Data[7]);
        sectionsPagerAdapter.updateHome(Data);
    }

    @Override
    public void onRunError(Exception e) {
        mainLooper.post(() -> {
            disconnect();
        });
    }

    private void disconnect() {
        connected = false;
        if (usbIoManager != null)
            usbIoManager.stop();
        usbIoManager = null;
        try {
            usbSerialPort.close();
        } catch (Exception Ignored) {
        }
        usbSerialPort = null;
        sectionsPagerAdapter.insertLog("Device disconnected");
        sectionsPagerAdapter.updateConnectionStatus(false);
    }

    private void connect() {
        Log.d("jmdmahdi:", "connect");
        UsbDevice device = null;
        UsbManager usbManager = (UsbManager) this.getSystemService(Context.USB_SERVICE);
        for (UsbDevice v : usbManager.getDeviceList().values())
            device = v;
        if (device == null) {
            Log.d("jmdmahdi:", "connection failed: device not found");
            return;
        }
        UsbSerialDriver driver;
        ProbeTable customTable = new ProbeTable();
        customTable.addProduct(5511, 63322, CdcAcmSerialDriver.class);
        driver = new UsbSerialProber(customTable).probeDevice(device);

        if (driver == null) {
            Log.d("jmdmahdi:", "connection failed: no driver for device");
            return;
        }

        usbSerialPort = driver.getPorts().get(0);

        UsbDeviceConnection usbConnection = usbManager.openDevice(driver.getDevice());
        if (usbConnection == null && usbPermission == UsbPermission.Unknown && !usbManager.hasPermission(driver.getDevice())) {
            usbPermission = UsbPermission.Requested;
            PendingIntent usbPermissionIntent = PendingIntent.getBroadcast(this, 0, new Intent(INTENT_ACTION_GRANT_USB), 0);
            usbManager.requestPermission(driver.getDevice(), usbPermissionIntent);
            return;
        }
        if (usbConnection == null) {
            if (!usbManager.hasPermission(driver.getDevice()))
                Log.d("jmdmahdi:", "connection failed: permission denied");
            else
                Log.d("jmdmahdi:", "connection failed: open failed");
            return;
        }

        try {
            usbSerialPort.open(usbConnection);
            usbSerialPort.setParameters(115200, 8, UsbSerialPort.STOPBITS_1, UsbSerialPort.PARITY_NONE);
            usbIoManager = new SerialInputOutputManager(usbSerialPort, this);
            Executors.newSingleThreadExecutor().submit(usbIoManager);
            Log.d("jmdmahdi:", "connected");
            connected = true;
            sectionsPagerAdapter.insertLog("Device connected");
            sectionsPagerAdapter.updateConnectionStatus(true);
        } catch (Exception e) {
            Log.d("jmdmahdi:", "connection failed: " + e.getMessage());
            disconnect();
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        if (intent.getAction().equals("android.hardware.usb.action.USB_DEVICE_ATTACHED")) {
            this.registerReceiver(broadcastReceiver, new IntentFilter(INTENT_ACTION_GRANT_USB));
            if (usbPermission == UsbPermission.Unknown || usbPermission == UsbPermission.Granted)
                mainLooper.post(this::connect);
        }
        super.onNewIntent(intent);
    }
}