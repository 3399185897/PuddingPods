import brut.androlib.mod.SmaliMod;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;

import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Minimal smali assembler that lets us pin the target API level.
 * apktool 2.11.1 always emits DEX 041 (Android 16 container format);
 * PUDDING runs on Android 15, so we force API 29 -> DEX 039.
 */
public final class DexAssembler {

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("usage: DexAssembler <smaliDir> <outDex> <apiLevel>");
            System.exit(2);
        }
        File root = new File(args[0]);
        File out = new File(args[1]);
        int api = Integer.parseInt(args[2]);

        List<File> files = new ArrayList<File>();
        walk(root, files);
        Collections.sort(files);
        if (files.isEmpty()) {
            System.err.println("no .smali files under " + root);
            System.exit(1);
        }

        DexBuilder dex = new DexBuilder(new Opcodes(api, 0));
        int done = 0;
        for (File f : files) {
            if (!SmaliMod.assembleSmaliFile(f, dex, api)) {
                System.err.println("FAILED: " + f.getPath());
                System.exit(1);
            }
            done++;
            if (done % 500 == 0) {
                System.out.println("  ... " + done + "/" + files.size());
            }
        }
        System.out.println("assembled " + done + " smali files");

        FileDataStore store = new FileDataStore(out);
        try {
            dex.writeTo(store);
        } finally {
            try {
                store.raf.close();
            } catch (Exception ignored) {
            }
        }
        System.out.println("dex written: " + out.getPath() + " (" + out.length() + " bytes)");
    }

    private static void walk(File dir, List<File> out) {
        File[] children = dir.listFiles();
        if (children == null) {
            return;
        }
        for (File f : children) {
            if (f.isDirectory()) {
                walk(f, out);
            } else if (f.getName().endsWith(".smali")) {
                out.add(f);
            }
        }
    }
}
