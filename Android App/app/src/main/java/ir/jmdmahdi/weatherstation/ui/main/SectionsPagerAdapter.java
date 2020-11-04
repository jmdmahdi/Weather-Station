package ir.jmdmahdi.weatherstation.ui.main;

import android.content.Context;
import android.os.Build;
import android.util.SparseArray;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.RequiresApi;
import androidx.annotation.StringRes;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentPagerAdapter;

import ir.jmdmahdi.weatherstation.R;

/**
 * A [FragmentPagerAdapter] that returns a fragment corresponding to
 * one of the sections/tabs/pages.
 */
public class SectionsPagerAdapter extends FragmentPagerAdapter {

    @StringRes
    private static final int[] TAB_TITLES = new int[]{R.string.tab_text_1, R.string.tab_text_2};
    private final Context mContext;
    SparseArray<Fragment> myPagerFragments = new SparseArray<>();

    public SectionsPagerAdapter(Context context, FragmentManager fm) {
        super(fm);
        mContext = context;
    }

    @Override
    public Fragment getItem(int position) {
        // getItem is called to instantiate the fragment for the given page.
        // Return a PlaceholderFragment (defined as a static inner class below).
        Fragment fragment;
        if (position == 0) {
            fragment = HomeFragment.newInstance(position);
        } else {
            fragment = LogFragment.newInstance(position);
        }
        myPagerFragments.put(position, fragment);
        return fragment;
    }

    public void insertLog(String text) {
        LogFragment Logfragment = (LogFragment) myPagerFragments.get(1);
        if (Logfragment != null)
            Logfragment.insertLog(text);
    }

    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    public void updateHome(float[] data) {
        HomeFragment homefragment = (HomeFragment) myPagerFragments.get(0);
        if (homefragment != null)
            homefragment.updateHome(data);
    }

    public void updateConnectionStatus(boolean status) {
        HomeFragment homefragment = (HomeFragment) myPagerFragments.get(0);
        if (homefragment != null)
            homefragment.updateConnectionStatus(status);
    }

    @Override
    public void destroyItem(@NonNull ViewGroup container, int position, @NonNull Object object) {
        myPagerFragments.remove(position);
        super.destroyItem(container, position, object);
    }

    @Nullable
    @Override
    public CharSequence getPageTitle(int position) {
        return mContext.getResources().getString(TAB_TITLES[position]);
    }

    @Override
    public int getCount() {
        // Show 2 total pages.
        return 2;
    }
}