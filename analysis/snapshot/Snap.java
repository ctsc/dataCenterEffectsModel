import java.awt.Component;
import java.awt.EventQueue;
import java.awt.Frame;
import java.awt.Window;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;
import org.nlogo.app.App;

/** Drive the NetLogo 7 GUI (Controlling API): open the model, apply settings, run, export the interface and
 *  paint every open window (including the System Dynamics Modeler) to PNG.
 *  Usage: java -cp "<netlogo app>/*;." Snap model.nlogox outdir name "cmd1" "cmd2" ... */
public class Snap {
    static void paint(Window w, File f) throws Exception {
        BufferedImage img = new BufferedImage(Math.max(1, w.getWidth()), Math.max(1, w.getHeight()), BufferedImage.TYPE_INT_RGB);
        EventQueue.invokeAndWait(() -> w.paint(img.getGraphics()));
        ImageIO.write(img, "png", f);
    }

    /** Decline NetLogo 7's first-run "Data Consent" (usage statistics) dialog so the run is unattended. */
    static boolean clickNo(java.awt.Container c) {
        for (Component k : c.getComponents()) {
            if (k instanceof javax.swing.AbstractButton && "No".equals(((javax.swing.AbstractButton) k).getText())) {
                ((javax.swing.AbstractButton) k).doClick();
                return true;
            }
            if (k instanceof java.awt.Container && clickNo((java.awt.Container) k)) return true;
        }
        return false;
    }

    public static void main(String[] a) throws Exception {
        String model = a[0], out = a[1], name = a[2];
        Thread t = new Thread(() -> {
            while (true) {
                for (Window w : Window.getWindows()) {
                    if (w instanceof java.awt.Dialog && w.isShowing() && "Data Consent".equals(((java.awt.Dialog) w).getTitle())) {
                        EventQueue.invokeLater(() -> clickNo(w));
                    }
                }
                try { Thread.sleep(300); } catch (InterruptedException e) { return; }
            }
        });
        t.setDaemon(true);
        t.start();
        App.main(new String[0]);
        EventQueue.invokeAndWait(() -> {
            try { App.app().open(model, true); } catch (Exception e) { throw new RuntimeException(e); }
        });
        App.app().command("setup");
        for (int i = 3; i < a.length; i++) App.app().command(a[i]);
        App.app().command("setup");
        App.app().command("while [ticks < 20] [ go ]");
        Thread.sleep(1500);
        String png = new File(out, name + ".png").getAbsolutePath().replace("\\", "/");
        App.app().command("export-interface \"" + png + "\"");
        if (name.endsWith("_1")) {
            int k = 0;
            for (Frame fr : Frame.getFrames()) {
                if (!fr.isShowing()) continue;
                if (fr.getTitle().contains("System Dynamics")) {
                    EventQueue.invokeAndWait(() -> { fr.setSize(1680, 1060); fr.validate(); });
                    Thread.sleep(1500);
                    paint(fr, new File(out, name + "_sd_modeler.png"));
                } else {
                    paint(fr, new File(out, name + "_window" + (k++) + ".png"));
                }
            }
            App.app().command("export-plot \"Load (MW)\" \"" + new File(out, name + "_load.csv").getAbsolutePath().replace("\\", "/") + "\"");
        }
        System.out.println("SNAP_DONE " + png);
        System.exit(0);
    }
}
