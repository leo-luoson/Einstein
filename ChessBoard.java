package einstein;  // 声明包名

import java.awt.*;          // AWT图形界面库
import java.awt.event.*;    // AWT事件处理
import javax.imageio.*;     // 图像I/O处理
import javax.swing.*;       // Swing GUI组件
import java.io.*;           // 文件输入输出
import java.nio.file.Paths; // 文件路径处理
import java.util.*;         // 工具类(Random, Scanner等)
import java.applet.*;       // Applet支持(实际未使用)

public class ChessBoard {
    // 添加这些变量替代suspend/resume
    private static volatile boolean threadPaused = true;
    private static final Object pauseLock = new Object();

    //核心GUI组件
    private static JFrame frame;           // 主窗口
    static JPanel panel[][] = new JPanel[5][5]; // 5x5棋盘格子
    private static JPanel imagePanel;      // 背景图片面板
    static ImageIcon background;           // 背景图片
    //按钮组件
    static JButton PlayerComputer = new JButton("人机对弈");    // 人机模式按钮
    static JButton PlayerPlayer = new JButton("人人对弈");      // 人人模式按钮
    static JButton ComputerComputer = new JButton("机人对弈");  // 机人模式按钮
    static JButton RandomChessSetting = new JButton("随机布局"); // 随机布局按钮
    static JButton ChessSetting = new JButton("手动布局");      // 手动布局按钮
    static JButton DifficultySetting = new JButton("难度设置"); // 难度设置按钮
    static JButton SeeLog = new JButton("显示/隐藏日志");       // 日志显示按钮
    //标签和文本组件
    static JLabel PlayerLabel = new JLabel("走棋方：");     // 当前玩家标签
    static JLabel DieLabel = new JLabel("骰子点数：");      // 骰子点数标签
    static JLabel DifficultyLabel = new JLabel("AI难度:普通"); // AI难度标签
    static JTextArea Log = new JTextArea();               // 日志文本区域
    static JScrollPane js = new JScrollPane();            // 日志滚动面板
    //日志系统
    //1.日志变量
    static String LogText = "欢迎信息";//显示的日志文本
    static String LogMsg;//完整日志消息
    static String LogComment="比赛信息头;";//日志注释头
    void initLog(String msg){
        LogComment=msg;
        LogRedLayout="R:";
        LogBlueLayout="B:";
        LogProcess="";
        ProcessNum=0;
    }
    static void initLog(){
        LogComment="#[WTN][Red Player R][Blue Player B][Chess Game][2018.08.04 14:00 Start][2018CCGC];;";
        LogRedLayout="R:";
        LogBlueLayout="B:";
        LogProcess="";
        ProcessNum=0;
    }
    static String LogRedLayout="R:";//红方布局记录
    static String LogBlueLayout="B:";//蓝方布局记录
    static void genLayoutLog(){
        for(int i=1;i<=6;i++){
            //noinspection StringConcatenationInLoop
            LogRedLayout+=(char)('A'+red[i][1])+""+(5-red[i][0])+"-"+i;
            LogBlueLayout+=(char)('A'+blue[i][1])+""+(5-blue[i][0])+"-"+i;
            if(i!=6){
                LogRedLayout+=";";
                LogBlueLayout+=";";
            }
        }
    }
    static String LogProcess="";
    static int ProcessNum=0;
    static void diffChessBoard(int bd1[][],int bd2[][]){
        boolean find=false;
        int a = 0,b = 0,x = 0,y = 0;
        for(int i=0;i<5;i++){
            for(int j=0;j<5;j++){
                if(bd1[i][j]!=bd2[i][j]){
                    if(bd2[i][j]==0){
                        a=i;
                        b=j;
                    }else{
                        x=i;
                        y=j;
                    }
                }
            }
        }
        if(a==0&&b==0&&x==0&&y==0)return;
        printRealDie=bd2[x][y];
        addProcessLog(a,b,x,y);
    }
    static void addProcessLog(int a,int b,int x,int y){
        //String msg=(++ProcessNum)+":"+Die+";("+(char)('A'+b)+(5-a)+','+(char)('A'+y)+(5-x)+')';
        ++ProcessNum;
        String role = ProcessNum%2==1? "R" : "B";
        if(role.equals("B")) {printRealDie-=6;}
        String msg=(ProcessNum)+":"+Die+";("+role+printRealDie+','+(char)('A'+y)+(5-x)+')';
        LogProcess+="\r\n"+msg;
    }

    static int printRealDie;
    static void saveLog(){
        LogMsg=LogComment+"\r\n"+LogRedLayout+"\r\n"+LogBlueLayout+LogProcess;

    }

    //核心游戏数据结构
    static int red[][] = new int[7][2];    // 红方6个棋子位置[棋子编号][x,y坐标]
    static int blue[][] = new int[7][2];   // 蓝方6个棋子位置[棋子编号][x,y坐标]
    static int NowColor;      // 当前选中棋子颜色(0=红,1=蓝)
    static int NowNumber;     // 当前选中棋子编号(1-6)
    static int NowX, NowY;    // 当前选中棋子位置
    static int Die;           // 当前骰子点数
    static int Mode = 0;      // 游戏模式(0=未选择,1=人机,2=人人,3=机机)
    static int Difficulty = 4; // AI难度(3=简单,4=普通,5=困难)
    static boolean PlayerMove = false;  // 是否轮到玩家移动
    static boolean Player1Move = true;  // 人人模式下是否轮到玩家1
    static boolean redExist, blueExist; // 红方蓝方是否还有棋子存活
    static boolean SeeLogFlag = false;  // 是否显示日志面板

    // 在main方法最开始添加编码设置
    public static void main(String[] args) throws InterruptedException, IOException {
        haveFun();
    }


    /**
     * Create the application.
     */
    public ChessBoard() {
        // 创建主窗口，设置大小和位置
        frame = new JFrame("Einstein Würfelt Nicht");
        frame.setBounds(460, 100, 435, 620);

        SeeLogFlag = false;
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);//关闭并退出程序
        frame.getContentPane().setLayout(null);

        // 设置背景图片
        background = new ImageIcon("background.jpg");
        JLabel label = new JLabel(background);
        label.setBounds(0, 0, background.getIconWidth(),
                background.getIconHeight());

        // 设置透明面板以显示背景
        imagePanel = (JPanel) frame.getContentPane();
        imagePanel.setOpaque(false);
        //MARK：修改
        frame.getLayeredPane().add(label, Integer.valueOf(Integer.MIN_VALUE));
        frame.setVisible(true);
        JOptionPane.showMessageDialog(frame, "欢迎使用爱因斯坦棋", "欢迎", JOptionPane.PLAIN_MESSAGE);
        frame.setVisible(false);

        initialize();
        t.start();
        // 原代码：t.suspend();
        pauseThread(); // 替换为新的暂停方法
    }
    //MARK：修改
    public static void pauseThread() {
        synchronized (pauseLock) {
            threadPaused = true;
        }
    }

    public static void resumeThread() {
        synchronized (pauseLock) {
            threadPaused = false;
            pauseLock.notifyAll();
        }
    }
    /**
     * Initialize the contents of the frame.
     */
    private static void initialize() {

        frame = new JFrame("Einstein Würfelt Nicht");
        frame.setBounds(460, 100, 435, 620);

        SeeLogFlag = false;
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);//关闭并退出程序
        frame.getContentPane().setLayout(null);

        // 设置背景图片
        background = new ImageIcon("background.jpg");
        JLabel label = new JLabel(background);
        label.setBounds(0, 0, background.getIconWidth(),
                background.getIconHeight());

        // 设置透明面板以显示背景
        imagePanel = (JPanel) frame.getContentPane();
        imagePanel.setOpaque(false);
        //MARK：修改
        frame.getLayeredPane().add(label, Integer.valueOf(Integer.MIN_VALUE));
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                panel[i][j] = new JPanel();
                if ((5 * i + j) % 2 == 0) {
                    panel[i][j] = new JPanelGrey();
                }
                else {
                    panel[i][j] = new JPanelWhite();
                }
                panel[i][j].setBounds(10 + j * 80, 10 + i * 80, 80, 80);
                frame.getContentPane().add(panel[i][j]);
            }
        }

        for (int k = 1; k <= 6; k++) {
            red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
        }

        PlayerComputer.removeActionListener(HandlerInitial);
        PlayerComputer.removeActionListener(HandlerPlayerComputer);
        PlayerPlayer.removeActionListener(HandlerInitial);
        PlayerPlayer.removeActionListener(HandlerPlayerPlayer);
        ComputerComputer.removeActionListener(HandlerInitial);
        ComputerComputer.removeActionListener(HandlerComputerComputer);
        DifficultySetting.removeActionListener(HandlerDifficultySetting);
        PlayerComputer.setBackground(Color.WHITE);
        PlayerComputer.setBounds(10, 425, 120, 40);
        PlayerComputer.addActionListener(HandlerInitial);
        frame.getContentPane().add(PlayerComputer);
        PlayerPlayer.setBackground(Color.WHITE);
        PlayerPlayer.setBounds(150, 425, 120, 40);
        PlayerPlayer.addActionListener(HandlerInitial);
        frame.getContentPane().add(PlayerPlayer);
        ComputerComputer.setBackground(Color.WHITE);
        ComputerComputer.setBounds(290, 425, 120, 40);
        ComputerComputer.addActionListener(HandlerInitial);
        frame.getContentPane().add(ComputerComputer);

        RandomChessSetting.removeActionListener(HandlerRandomChessSetting);
        ChessSetting.removeActionListener(HandlerChessSetting);
        RandomChessSetting.setBackground(Color.WHITE);
        RandomChessSetting.setBounds(10, 480, 90, 40);
        RandomChessSetting.addActionListener(HandlerRandomChessSetting);
        frame.getContentPane().add(RandomChessSetting);
        ChessSetting.setBackground(Color.WHITE);
        ChessSetting.setBounds(110, 480, 90, 40);
        ChessSetting.addActionListener(HandlerChessSetting);
        frame.getContentPane().add(ChessSetting);
        DifficultySetting.setBackground(Color.WHITE);
        DifficultySetting.setBounds(210, 480, 90, 40);
        DifficultySetting.addActionListener(HandlerDifficultySetting);
        frame.getContentPane().add(DifficultySetting);
        SeeLog.removeActionListener(HandlerSeeLog);
        SeeLog.setBackground(Color.WHITE);
        SeeLog.setBounds(310, 480, 100, 40);
        SeeLog.addActionListener(HandlerSeeLog);
        frame.getContentPane().add(SeeLog);

        Font font = new Font("Microsoft YaHei", Font.BOLD, 20);
        PlayerLabel.setFont(font);
        PlayerLabel.setText("走棋方：");
        PlayerLabel.setBounds(20, 530, 120, 40);
        PlayerLabel.updateUI();
        frame.getContentPane().add(PlayerLabel);

        DieLabel.setFont(font);
        DieLabel.setText("骰子点数：");
        DieLabel.setBounds(165, 530, 120, 40);
        DieLabel.updateUI();
        frame.getContentPane().add(DieLabel);

        DifficultyLabel.setFont(font);
        DifficultyLabel.setBounds(290, 530, 120, 40);
        frame.getContentPane().add(DifficultyLabel);

        Font font1 = new Font("Microsoft YaHei", Font.BOLD, 13);
        Log.setFont(font1);
        Log.setBackground(new Color(220, 220, 220));
        Log.setText(LogText);
        Log.setEditable(false);
        Log.updateUI();

        js.setViewportView(Log);
        js.setBounds(420, 10, 175, 550);
        frame.getContentPane().add(js);
        drawSituation();
    }

    private static void randomChessSetting() {
        PlayerComputer.removeActionListener(HandlerInitial);
        PlayerComputer.removeActionListener(HandlerPlayerComputer);
        PlayerPlayer.removeActionListener(HandlerInitial);
        PlayerPlayer.removeActionListener(HandlerPlayerPlayer);
        ComputerComputer.removeActionListener(HandlerInitial);
        ComputerComputer.removeActionListener(HandlerComputerComputer);
        PlayerComputer.addActionListener(HandlerPlayerComputer);
        PlayerPlayer.addActionListener(HandlerPlayerPlayer);
        ComputerComputer.addActionListener(HandlerComputerComputer);

        Random die = new Random();
        int x;
        boolean flag[] = new boolean[7];
        for (int i = 1; i <= 6; i++) {
            flag[i] = false;
        }
        flag[0] = true;
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3 - i; j++) {
                x = 0;
                while (flag[x]) {
                    x = die.nextInt(6) + 1;
                }
                flag[x] = true;
                red[x][0] = i; red[x][1] = j;
            }
        }
        for (int i = 1; i <= 6; i++) {
            flag[i] = false;
        }
        flag[0] = true;
        for (int i = 2; i < 5; i++) {
            for (int j = 4; j >= 6 - i; j--) {
                x = 0;
                while (flag[x]) {
                    x = die.nextInt(6) + 1;
                }
                flag[x] = true;
                blue[x][0] = i; blue[x][1] = j;
            }
        }
        LogText += "随机布局：\n";
        int pos[][] = new int[5][5];
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                pos[i][j] = 0;
                for (int k = 1; k <= 6; k++) {
                    if (red[k][0] == i && red[k][1] == j) {
                        pos[i][j] = k;
                        break;
                    }
                    if (blue[k][0] == i && blue[k][1] == j) {
                        pos[i][j] = k + 6;
                        break;
                    }
                }
            }
        }
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                char c;
                if (j == 4) c = '\n';
                else c = ' ';
                LogText += pos[i][j] + "" + c;
            }
        }
        LogText += "\n";
        Log.setText(LogText);

        initLog();
        genLayoutLog();
        saveLog();
        Log.setText(LogMsg);

    }
    private static void chessSetting() {
        PlayerComputer.removeActionListener(HandlerInitial);
        PlayerComputer.removeActionListener(HandlerPlayerComputer);
        PlayerPlayer.removeActionListener(HandlerInitial);
        PlayerPlayer.removeActionListener(HandlerPlayerPlayer);
        ComputerComputer.removeActionListener(HandlerInitial);
        ComputerComputer.removeActionListener(HandlerComputerComputer);
        PlayerComputer.addActionListener(HandlerPlayerComputer);
        PlayerPlayer.addActionListener(HandlerPlayerPlayer);
        ComputerComputer.addActionListener(HandlerComputerComputer);
        for (int k = 1; k <= 6; k++) {
            red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
        }
        drawSituation();
        String input = null;
        int x;
        boolean flag[] = new boolean[7];
        for (int i = 1; i <= 6; i++) {
            flag[i] = false;
        }
        flag[0] = true;
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3 - i; j++) {
                x = 0;
                while (!(x >= 0 && x <= 6) || flag[x]) {
                    input = JOptionPane.showInputDialog
                            (frame, "请在位置(" + i + "," + j + ")放入未放置的红方棋子编号:",
                                    "手动布局", JOptionPane.PLAIN_MESSAGE);
                    x = Integer.parseInt(input);
                }
                flag[x] = true;
                red[x][0] = i; red[x][1] = j;
                drawSituation();
            }
        }
        for (int i = 1; i <= 6; i++) {
            flag[i] = false;
        }
        flag[0] = true;
        for (int i = 2; i < 5; i++) {
            for (int j = 4; j >= 6 - i; j--) {
                x = 0;
                while (!(x >= 0 && x <= 6) || flag[x]) {
                    input = JOptionPane.showInputDialog
                            (frame, "请在位置(" + i + "," + j + ")放入未放置的蓝方棋子:",
                                    "手动布局", JOptionPane.PLAIN_MESSAGE);
                    x = Integer.parseInt(input);
                }
                flag[x] = true;
                blue[x][0] = i; blue[x][1] = j;
                drawSituation();
            }
        }
        LogText += "手动布局：\n";
        int pos[][] = new int[5][5];
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                pos[i][j] = 0;
                for (int k = 1; k <= 6; k++) {
                    if (red[k][0] == i && red[k][1] == j) {
                        pos[i][j] = k;
                        break;
                    }
                    if (blue[k][0] == i && blue[k][1] == j) {
                        pos[i][j] = k + 6;
                        break;
                    }
                }
            }
        }
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                char c;
                if (j == 4) c = '\n';
                else c = ' ';
                LogText += pos[i][j] + "" + c;
            }
        }
        LogText += "\n";
        Log.setText(LogText);

        initLog();
        genLayoutLog();
        saveLog();
        Log.setText(LogMsg);
    }
    private static boolean inChessBoard(int x, int y) {
        return x >= 0 && x < 5 && y >= 0 && y < 5;
    }
    private static boolean canMove(int x) {
        if (Mode == 1) {
            if (x == Die) return true;
            int k;
            for (k = Die; k <= 6; k++) {
                if (red[k][0] != -1) {
                    break;
                }
            }
            if (k == x) return true;
            for (k = Die; k > 0; k--) {
                if (red[k][0] != -1) {
                    break;
                }
            }
            if (k == x) return true;
            return false;
        }
        else if (Mode == 2){
            if (Player1Move) {
                if (NowColor == 1) return false;
                if (x == Die) return true;
                int k;
                for (k = Die; k <= 6; k++) {
                    if (red[k][0] != -1) {
                        break;
                    }
                }
                if (k == x) return true;
                for (k = Die; k > 0; k--) {
                    if (red[k][0] != -1) {
                        break;
                    }
                }
                if (k == x) return true;
                return false;
            }
            else {
                if (NowColor == 0) return false;
                if (x == Die) return true;
                int k;
                for (k = Die; k <= 6; k++) {
                    if (blue[k][0] != -1) {
                        break;
                    }
                }
                if (k == x) return true;
                for (k = Die; k > 0; k--) {
                    if (blue[k][0] != -1) {
                        break;
                    }
                }
                if (k == x) return true;
                return false;
            }
        }
        else if (Mode == 3) {
            if (x == Die) return true;
            int k;
            for (k = Die; k <= 6; k++) {
                if (blue[k][0] != -1) {
                    break;
                }
            }
            if (k == x) return true;
            for (k = Die; k > 0; k--) {
                if (blue[k][0] != -1) {
                    break;
                }
            }
            if (k == x) return true;
            return false;
        }
        return false;
    }
    private static void biaoJi() {
        int x, y;
        if (Mode == 1) {
            for (int k = 1; k <= 6; k++) {
                if (red[k][0] != -1 && red[k][1] != -1) {
                    boolean flag = false;
                    if (k == Die) flag = true;
                    int l;
                    for (l = Die; l <= 6; l++) {
                        if (red[l][0] != -1) {
                            break;
                        }
                    }
                    if (l == k) flag = true;
                    for (l = Die; l > 0; l--) {
                        if (red[l][0] != -1) {
                            break;
                        }
                    }
                    if (l == k) flag = true;
                    if (flag) {
                        x = red[k][0]; y = red[k][1];
                        frame.getContentPane().remove(panel[x][y]);
                        if ((5 * x + y) % 2 == 0) {
                            panel[x][y] = new JPanelGreyChess(2, k);
                        }
                        else {
                            panel[x][y] = new JPanelWhiteChess(2, k);
                        }
                        panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                        panel[x][y].removeMouseListener(HandlerSelect);
                        panel[x][y].removeMouseListener(HandlerMove);
                        panel[x][y].removeMouseListener(HandlerFailMove);
                        panel[x][y].addMouseListener(HandlerSelect);
                        frame.getContentPane().add(panel[x][y]);
                        panel[x][y].repaint();
                    }
                }
            }
        }
        if (Mode == 3) {
            for (int k = 1; k <= 6; k++) {
                if (blue[k][0] != -1 && blue[k][1] != -1) {
                    boolean flag = false;
                    if (k == Die) flag = true;
                    int l;
                    for (l = Die; l <= 6; l++) {
                        if (blue[l][0] != -1) {
                            break;
                        }
                    }
                    if (l == k) flag = true;
                    for (l = Die; l > 0; l--) {
                        if (blue[l][0] != -1) {
                            break;
                        }
                    }
                    if (l == k) flag = true;
                    if (flag) {
                        x = blue[k][0]; y = blue[k][1];
                        frame.getContentPane().remove(panel[x][y]);
                        if ((5 * x + y) % 2 == 0) {
                            panel[x][y] = new JPanelGreyChess(3, k);
                            //System.out.println("ok1");
                        }
                        else {
                            panel[x][y] = new JPanelWhiteChess(3, k);
                            //System.out.println("ok1");
                        }
                        panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                        panel[x][y].removeMouseListener(HandlerSelect);
                        panel[x][y].removeMouseListener(HandlerMove);
                        panel[x][y].removeMouseListener(HandlerFailMove);
                        panel[x][y].addMouseListener(HandlerSelect);
                        frame.getContentPane().add(panel[x][y]);
                        panel[x][y].repaint();
                    }
                }
            }
        }
        if (Mode == 2) {
            if (Player1Move) {
                for (int k = 1; k <= 6; k++) {
                    if (red[k][0] != -1 && red[k][1] != -1) {
                        boolean flag = false;
                        if (k == Die) flag = true;
                        int l;
                        for (l = Die; l <= 6; l++) {
                            if (red[l][0] != -1) {
                                break;
                            }
                        }
                        if (l == k) flag = true;
                        for (l = Die; l > 0; l--) {
                            if (red[l][0] != -1) {
                                break;
                            }
                        }
                        if (l == k) flag = true;
                        if (flag) {
                            x = red[k][0]; y = red[k][1];
                            frame.getContentPane().remove(panel[x][y]);
                            if ((5 * x + y) % 2 == 0) {
                                //System.out.println("ok");
                                panel[x][y] = new JPanelGreyChess(2, k);
                            }
                            else {
                                //System.out.println("ok");
                                panel[x][y] = new JPanelWhiteChess(2, k);
                            }
                            panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                            panel[x][y].removeMouseListener(HandlerSelect);
                            panel[x][y].removeMouseListener(HandlerMove);
                            panel[x][y].removeMouseListener(HandlerFailMove);
                            panel[x][y].addMouseListener(HandlerSelect);
                            frame.getContentPane().add(panel[x][y]);
                            panel[x][y].repaint();
                        }
                    }
                }
            }
            else {
                for (int k = 1; k <= 6; k++) {
                    if (blue[k][0] != -1 && blue[k][1] != -1) {
                        boolean flag = false;
                        if (k == Die) flag = true;
                        int l;
                        for (l = Die; l <= 6; l++) {
                            if (blue[l][0] != -1) {
                                break;
                            }
                        }
                        if (l == k) flag = true;
                        for (l = Die; l > 0; l--) {
                            if (blue[l][0] != -1) {
                                break;
                            }
                        }
                        if (l == k) flag = true;
                        if (flag) {
                            x = blue[k][0]; y = blue[k][1];
                            frame.getContentPane().remove(panel[x][y]);
                            if ((5 * x + y) % 2 == 0) {
                                panel[x][y] = new JPanelGreyChess(3, k);
                                //System.out.println("ok1");
                            }
                            else {
                                panel[x][y] = new JPanelWhiteChess(3, k);
                                //System.out.println("ok1");
                            }
                            panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                            panel[x][y].removeMouseListener(HandlerSelect);
                            panel[x][y].removeMouseListener(HandlerMove);
                            panel[x][y].removeMouseListener(HandlerFailMove);
                            panel[x][y].addMouseListener(HandlerSelect);
                            frame.getContentPane().add(panel[x][y]);
                            panel[x][y].repaint();
                        }
                    }
                }
            }
        }
    }
    //MARK：修改
    public static class ThreadTest1 implements Runnable {
        public void run() {
            while (true) {
                // 检查是否需要暂停
                synchronized (pauseLock) {
                    while (threadPaused) {
                        try {
                            pauseLock.wait(); // 等待恢复信号
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            return;
                        }
                    }
                }

                // 原有的闪烁逻辑保持不变
                frame.getContentPane().remove(panel[NowX][NowY]);
                if ((5 * NowX + NowY) % 2 == 0) {
                    panel[NowX][NowY] = new JPanelGreyChess(NowColor, NowNumber);
                } else {
                    panel[NowX][NowY] = new JPanelWhiteChess(NowColor, NowNumber);
                }
                panel[NowX][NowY].setBounds(10 + NowY * 80, 10 + NowX * 80, 80, 80);
                frame.getContentPane().add(panel[NowX][NowY]);
                panel[NowX][NowY].repaint();

                try {
                    Thread.sleep(600);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }

                frame.getContentPane().remove(panel[NowX][NowY]);
                if ((5 * NowX + NowY) % 2 == 0) {
                    panel[NowX][NowY] = new JPanelGrey();
                } else {
                    panel[NowX][NowY] = new JPanelWhite();
                }
                panel[NowX][NowY].setBounds(10 + NowY * 80, 10 + NowX * 80, 80, 80);
                frame.getContentPane().add(panel[NowX][NowY]);
                panel[NowX][NowY].repaint();

                try {
                    Thread.sleep(400);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
    }
    public static ThreadTest1 tt = new ThreadTest1();
    public static Thread t = new Thread(tt);
    private static boolean over() {
        //到达目的地结束游戏
        for (int k = 1; k <= 6; k++) {
            if (red[k][0] == 4 && red[k][1] == 4) {
                JOptionPane.showMessageDialog(frame, "     Game Over!  Red wins!", "战斗结果", JOptionPane.PLAIN_MESSAGE);
                LogText += "游戏结束结果： 红方胜\n\n";
                Log.setText(LogText);
                return true;
            }
            if (blue[k][0] == 0 && blue[k][1] == 0) {
                JOptionPane.showMessageDialog(frame, "     Game Over!  Blue wins!", "战斗结果", JOptionPane.PLAIN_MESSAGE);
                LogText += "游戏结束结果： 蓝方胜\n\n";
                Log.setText(LogText);
                return true;
            }
        }

        redExist = false; blueExist = false;
        for (int k = 1; k <= 6; k++) {
            if (red[k][0] != -1 || red[k][1] != -1) {
                redExist = true;
                break;
            }
        }
        if (redExist == false) {
            JOptionPane.showMessageDialog(frame, "     Game Over!  Blue wins!", "战斗结果", JOptionPane.PLAIN_MESSAGE);
            LogText += "游戏结束结果： 蓝方胜\n\n";
            Log.setText(LogText);
            return true;
        }
        for (int k = 1; k <= 6; k++) {
            if (blue[k][0] != -1 || blue[k][1] != -1) {
                blueExist = true;
                break;
            }
        }
        if (blueExist == false) {
            JOptionPane.showMessageDialog(frame, "     Game Over!  Red wins!", "战斗结果", JOptionPane.PLAIN_MESSAGE);
            LogText += "游戏结束结果： 红方胜\n\n";
            Log.setText(LogText);
            return true;
        }
        return false;
    }
    private static MouseAdapter HandlerSelect = new MouseAdapter() {

        public void mouseClicked(MouseEvent e) {
//			t_haveFun.suspend();
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    if (panel[i][j] == e.getSource()) {
                        NowX = i; NowY = j;
                        for (int k = 1; k <= 6; k++) {
                            if (red[k][0] == i && red[k][1] == j) {
                                NowColor = 0; NowNumber = k;
                                break;
                            }
                            if (blue[k][0] == i && blue[k][1] == j) {
                                NowColor = 1; NowNumber = k;
                                break;
                            }
                        }
                        if (Mode == 1) {
                            if (NowColor == 1) return;
                        }
                        if (Mode == 3) {
                            if (NowColor == 0) return;
                        }
                        if (canMove(NowNumber)) {
                            if (NowColor == 0) {
                                if (inChessBoard(i, j + 1)) {
                                    panel[i][j + 1].removeMouseListener(HandlerSelect);
                                    panel[i][j + 1].removeMouseListener(HandlerMove);
                                    panel[i][j + 1].removeMouseListener(HandlerFailMove);
                                    panel[i][j + 1].addMouseListener(HandlerMove);
                                }
                                if (inChessBoard(i + 1, j)) {
                                    panel[i + 1][j].removeMouseListener(HandlerSelect);
                                    panel[i + 1][j].removeMouseListener(HandlerMove);
                                    panel[i + 1][j].removeMouseListener(HandlerFailMove);
                                    panel[i + 1][j].addMouseListener(HandlerMove);
                                }
                                if (inChessBoard(i + 1, j + 1)) {
                                    panel[i + 1][j + 1].removeMouseListener(HandlerSelect);
                                    panel[i + 1][j + 1].removeMouseListener(HandlerMove);
                                    panel[i + 1][j + 1].removeMouseListener(HandlerFailMove);
                                    panel[i + 1][j + 1].addMouseListener(HandlerMove);
                                }
                                for (int ii = 0; ii < 5; ii++) {
                                    for (int jj = 0; jj < 5; jj++) {
                                        if (!((ii == NowX && jj == NowY + 1)
                                                || (ii == NowX + 1 && jj == NowY)
                                                || (ii == NowX + 1 && jj == NowY + 1))) {
                                            panel[ii][jj].removeMouseListener(HandlerSelect);
                                            panel[ii][jj].removeMouseListener(HandlerMove);
                                            panel[ii][jj].removeMouseListener(HandlerFailMove);
                                            panel[ii][jj].addMouseListener(HandlerFailMove);
                                        }
                                    }
                                }
                            }
                            else {
                                if (inChessBoard(i, j - 1)) {
                                    panel[i][j - 1].removeMouseListener(HandlerSelect);
                                    panel[i][j - 1].removeMouseListener(HandlerMove);
                                    panel[i][j - 1].removeMouseListener(HandlerFailMove);
                                    panel[i][j - 1].addMouseListener(HandlerMove);
                                }
                                if (inChessBoard(i - 1, j)) {
                                    panel[i - 1][j].removeMouseListener(HandlerSelect);
                                    panel[i - 1][j].removeMouseListener(HandlerMove);
                                    panel[i - 1][j].removeMouseListener(HandlerFailMove);
                                    panel[i - 1][j].addMouseListener(HandlerMove);
                                }
                                if (inChessBoard(i - 1, j - 1)) {
                                    panel[i - 1][j - 1].removeMouseListener(HandlerSelect);
                                    panel[i - 1][j - 1].removeMouseListener(HandlerMove);
                                    panel[i - 1][j - 1].removeMouseListener(HandlerFailMove);
                                    panel[i - 1][j - 1].addMouseListener(HandlerMove);
                                }
                                for (int ii = 0; ii < 5; ii++) {
                                    for (int jj = 0; jj < 5; jj++) {
                                        if (!((ii == NowX && jj == NowY - 1)
                                                || (ii == NowX - 1 && jj == NowY)
                                                || (ii == NowX - 1 && jj == NowY - 1))) {
                                            panel[ii][jj].removeMouseListener(HandlerSelect);
                                            panel[ii][jj].removeMouseListener(HandlerMove);
                                            panel[ii][jj].removeMouseListener(HandlerFailMove);
                                            panel[ii][jj].addMouseListener(HandlerFailMove);
                                        }
                                    }
                                }
                            }
                            //MARK:修改
                            resumeThread();
                        }
                    }
                }
            }
        }
    };
    private static MouseAdapter HandlerMove = new MouseAdapter() {

        public void mouseClicked(MouseEvent e) {
            //MARK：修改
            pauseThread();
            frame.getContentPane().remove(panel[NowX][NowY]);
            if ((5 * NowX + NowY) % 2 == 0) {
                panel[NowX][NowY] = new JPanelGrey();
            }
            else {
                panel[NowX][NowY] = new JPanelWhite();
            }
            panel[NowX][NowY].setBounds(10 + NowY * 80, 10 + NowX * 80, 80, 80);
            frame.getContentPane().add(panel[NowX][NowY]);
            panel[NowX][NowY].repaint();

            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    if (panel[i][j] == e.getSource()) {
                        for (int k = 1; k <= 6; k++) {
                            if (red[k][0] == i && red[k][1] == j) {
                                red[k][0] = -1; red[k][1] = -1;
                                break;
                            }
                            if (blue[k][0] == i && blue[k][1] == j) {
                                blue[k][0] = -1; blue[k][1] = -1;
                                break;
                            }
                        }
                        if (NowColor == 0) {
                            red[NowNumber][0] = i; red[NowNumber][1] = j;
                        }
                        else {
                            blue[NowNumber][0] = i; blue[NowNumber][1] = j;
                        }

                        if (Mode == 1) PlayerMove = true;
                        else if (Mode == 2) Player1Move = !Player1Move;
                        else if(Mode == 3) PlayerMove = true;

                        frame.getContentPane().remove(panel[i][j]);
                        if ((5 * i + j) % 2 == 0) {
                            panel[i][j] = new JPanelGreyChess(NowColor, NowNumber);
                        }
                        else {
                            panel[i][j] = new JPanelWhiteChess(NowColor, NowNumber);
                        }
                        panel[i][j].setBounds(10 + j * 80, 10 + i * 80, 80, 80);
                        frame.getContentPane().add(panel[i][j]);
                        panel[i][j].repaint();
                        for (int ii = 0; ii < 5; ii++) {
                            for (int jj = 0; jj < 5; jj++) {
                                panel[ii][jj].removeMouseListener(HandlerSelect);
                                panel[ii][jj].removeMouseListener(HandlerMove);
                                panel[ii][jj].removeMouseListener(HandlerFailMove);
                                for (int k = 1; k <= 6; k++) {
                                    if ((red[k][0] == ii && red[k][1] == jj)
                                            || (blue[k][0] == ii && blue[k][1] == jj)) {
                                        panel[ii][jj].addMouseListener(HandlerSelect);
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            drawSituation();
        }
    };
    private static MouseAdapter HandlerFailMove = new MouseAdapter() {
        public void mouseClicked(MouseEvent e) {
            //MARK：修改
            pauseThread();
            frame.getContentPane().remove(panel[NowX][NowY]);
            if ((5 * NowX + NowY) % 2 == 0) {
                panel[NowX][NowY] = new JPanelGreyChess(NowColor, NowNumber);
            }
            else {
                panel[NowX][NowY] = new JPanelWhiteChess(NowColor, NowNumber);
            }
            panel[NowX][NowY].setBounds(10 + NowY * 80, 10 + NowX * 80, 80, 80);
            frame.getContentPane().add(panel[NowX][NowY]);
            panel[NowX][NowY].repaint();
            for (int ii = 0; ii < 5; ii++) {
                for (int jj = 0; jj < 5; jj++) {
                    panel[ii][jj].removeMouseListener(HandlerSelect);
                    panel[ii][jj].removeMouseListener(HandlerMove);
                    panel[ii][jj].removeMouseListener(HandlerFailMove);
                    for (int k = 1; k <= 6; k++) {
                        if ((red[k][0] == ii && red[k][1] == jj)
                                || (blue[k][0] == ii && blue[k][1] == jj)) {
                            panel[ii][jj].addMouseListener(HandlerSelect);
                            break;
                        }
                    }
                }
            }
            biaoJi();
        }
    };
    private static ActionListener HandlerPlayerComputer = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            Mode = 1;
        }
    };
    private static ActionListener HandlerPlayerPlayer = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            Mode = 2;
        }
    };
    private static ActionListener HandlerComputerComputer = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            Mode = 3;
        }
    };
    private static ActionListener HandlerRandomChessSetting = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            randomChessSetting();
            drawSituation();
        }
    };
    private static ActionListener HandlerChessSetting = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            chessSetting();
            drawSituation();
        }
    };
    private static ActionListener HandlerInitial = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            JOptionPane.showMessageDialog(frame, "请先布局再开始游戏！");
        }
    };
    private static ActionListener HandlerDifficultySetting = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            String input = null, text = null;
            int x = 0;
            while (!(x >= 1 && x <= 3)) {
                input = JOptionPane.showInputDialog
                        (frame, "请选择一个难度选项 难度:\n(1) easy\n(2) normal\n(3) hard\n",
                                "难度设置", JOptionPane.PLAIN_MESSAGE);
                x = Integer.parseInt(input);
                if (x >= 1 && x <= 3) break;
            }
            Difficulty = x + 2;
            if (Difficulty == 3) {
                text = "简单";
                LogText += "当前AI难度为: 简单\n";
            }
            if (Difficulty == 4) {
                text = "普通";
                LogText += "当前AI难度为: 普通\n";
            }
            if (Difficulty == 5) {
                text = "困难";
                LogText += "当前AI难度为: 困难\n";
            }
            text = "AI难度: " + text;
            DifficultyLabel.setText(text);
            LogText += "\n";
            Log.setText(LogText);
        }
    };
    private static ActionListener HandlerSeeLog = new ActionListener() {
        public void actionPerformed(ActionEvent e) {
            if (SeeLogFlag) {
                frame.setBounds(460, 100, 435, 620);
                SeeLogFlag = false;
            }
            else {
                frame.setBounds(460, 100, 620, 620);
                SeeLogFlag = true;
            }
        }
    };
    private static void playerVsComputer() throws IOException, InterruptedException {
        RandomChessSetting.removeActionListener(HandlerRandomChessSetting);
        ChessSetting.removeActionListener(HandlerChessSetting);
        DifficultySetting.removeActionListener(HandlerDifficultySetting);
        LogText += "游戏开始-人机对战\n";
        Log.setText(LogText);

        saveLog();
        Log.setText(LogMsg);

        JOptionPane.showMessageDialog(frame, "游戏开始-人机对战");
        String ipx;
        int x = 0;
        boolean first = true;
        if (x == 0) LogText += "你已选择先手走棋\n\n";
        else LogText += "你已选择后手走棋\n\n";
        Log.setText(LogText);

        saveLog();
        Log.setText(LogMsg);

        if (x == 0) PlayerMove = false;
        else PlayerMove = true;
        //Random random = new Random();
        int key=0;
        while (true) {
            //print log
            int countkey=0;
            PrintWriter LogPrinter = new PrintWriter("Log.txt");
            saveLog();
            LogPrinter.print(LogMsg);
            LogPrinter.close();
            if (over()){
                return;
            }
            if (!PlayerMove) {
                //Die = random.nextInt(6) + 1;
                Die=0;
                while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                    ipx=JOptionPane.showInputDialog
                            (frame, "请输入骰子点数ֵ",
                                    "1-6", JOptionPane.PLAIN_MESSAGE);
                    try{
                        Die=Integer.parseInt(ipx);
                    }catch(Exception e){
                        Die=0;
                    }
                }
                PlayerLabel.setText("走棋方: 红方");
                DieLabel.setText("骰子点数: " + Die);
                //JOptionPane.showMessageDialog(null, "Your die:  " + Die);
                LogText += "Player's die: " + Die + "\n";
                Log.setText(LogText);

                saveLog();
                Log.setText(LogMsg);

                biaoJi();
            }

            int bd1[][] = new int[5][5];
            int bd2[][] = new int[5][5];
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    bd1[i][j] = 0;
                    for (int k = 1; k <= 6; k++) {
                        if (red[k][0] == i && red[k][1] == j) {
                            bd1[i][j] = k;
                            break;
                        }
                        if (blue[k][0] == i && blue[k][1] == j) {
                            bd1[i][j] = k + 6;
                            break;
                        }
                    }
                }
            }
            while (true) {
                Scanner input1 = new Scanner(System.in);
                if (PlayerMove) {
                    //System.out.println("ok");
                    int pos[][] = new int[5][5];
                    if (x == 0 || !first) {

                        for (int i = 0; i < 5; i++) {
                            for (int j = 0; j < 5; j++) {
                                pos[i][j] = 0;
                                for (int k = 1; k <= 6; k++) {
                                    if (red[k][0] == i && red[k][1] == j) {
                                        pos[i][j] = k;
                                        break;
                                    }
                                    if (blue[k][0] == i && blue[k][1] == j) {
                                        pos[i][j] = k + 6;
                                        break;
                                    }
                                }
                            }
                        }
                        for (int i = 0; i < 5; i++) {
                            for (int j = 0; j < 5; j++) {
                                char c;
                                if (j == 4) c = '\n';
                                else c = ' ';
                                LogText += pos[i][j] + "" + c;
                            }
                        }
                        LogText += "\n";
                        Log.setText(LogText);

                        for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd2[i][j]=pos[i][j];
                        diffChessBoard(bd1,bd2);
                        saveLog();
                        for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd1[i][j]=bd2[i][j];
                        Log.setText(LogMsg);
                    }
                    first = false;

                    if (over()) return;


                    //System.out.println("ok");
                    //Die = random.nextInt(6) + 1;
                    Die=0;
                    while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                        ipx=JOptionPane.showInputDialog
                                (frame, "请输入骰子点数ֵ",
                                        "1-6", JOptionPane.PLAIN_MESSAGE);
                        try{
                            Die=Integer.parseInt(ipx);
                        }catch(Exception e){
                            Die=0;
                        }
                    }
                    PlayerLabel.setText("走棋方: 蓝方");
                    DieLabel.setText("骰子点数: " + Die);
                    //JOptionPane.showMessageDialog(null, "Computer's die:  " + Die);
                    LogText += "Computer's die: " + Die + "\n";
                    Log.setText(LogText);

                    saveLog();
                    Log.setText(LogMsg);
                    PrintWriter output = new PrintWriter("JavaOut.txt");
                    output.println(Difficulty + " " + Die);
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            int k;
                            for (k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    output.print(k);
                                    if (j != 4) output.print(" ");
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    output.print(k + 6);
                                    if (j != 4) output.print(" ");
                                    break;
                                }
                            }
                            if (k == 7) {
                                output.print(0);
                                if (j != 4) output.print(" ");
                            }
                        }
                        output.println();
                    }
                    //output.println( " " + Die);
                    PlayerMove = false;
                    output.close();








                    PrintWriter output3 = new PrintWriter("JavaOut1.txt");
                    //output.println(Difficulty + " " + Die);
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            int k;
                            for (k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    output3.print(k);
                                    if (j != 4) output3.print(" ");
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    output3.print(k + 6);
                                    if (j != 4) output3.print(" ");
                                    break;
                                }
                            }
                            if (k == 7) {
                                output3.print(0);
                                if (j != 4) output3.print(" ");
                            }
                        }
                        output3.println();
                    }
                    output3.println( " " + Die);

                    output3.close();
//				PrintWriter output2 = new PrintWriter("Flag.txt");
//				output2.println("0");
//				output2.close();

//				Runtime Rt = Runtime.getRuntime();
//				File myfile = new File("EinsteinAI.exe");
//				Rt.exec(myfile.getAbsolutePath());

                    //Process p = Runtime.getRuntime().exec("EinsteinAI.exe");
                    if(key==0) {Process p = Runtime.getRuntime().exec("estout.exe");
                        p.waitFor();}
                    if(key==1) {Process p = Runtime.getRuntime().exec("EinsteinAI.exe");
                        p.waitFor();}
                    //System.out.println("ok1");

//				Scanner input2 = null;
//				int flag;
//				//while (flag == 0) {
//					input2 = new Scanner(Paths.get("Flag.txt"));
//					flag = input2.nextInt();
//					System.out.println("ok2");
//					input2.close();
//				//}
//				System.out.println(flag);
//
//				System.out.println("ok3");


                    Scanner input = new Scanner(Paths.get("JavaIn.txt"));
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            pos[i][j] = input.nextInt();
                        }
                    }
                    input.close();




                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            if(pos[i][j]>6&&pos[i][j]<=12) {
                                countkey++;
                            }
                        }
                    }
                    if(countkey<=3) {
                        key=1;
                    }
				/*if(countkey==1) {
					key=0;
				}*/
                    for(int i=0;i<5;i++){
                        for(int j=0;j<5;j++){
                            bd2[i][j]=pos[i][j];
                        }
                    }

                    for (int k = 1; k <= 6; k++) {
                        red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
                    }
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            //System.out.print(pos[i][j]);
                            //System.out.print(" ");
                            if (pos[i][j] >= 1 && pos[i][j] <= 6) {
                                red[pos[i][j]][0] = i;
                                red[pos[i][j]][1] = j;
                            }
                            if (pos[i][j] >= 7 && pos[i][j] <= 12) {
                                blue[pos[i][j] - 6][0] = i;
                                blue[pos[i][j] - 6][1] = j;
                            }
                        }
                        //System.out.println();
                    }
                    //System.out.println(blue[1][0] + " " + blue[1][1]);
                    //System.out.println(blue[2][0] + " " + blue[2][1]);

                    drawSituation();

                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            char c;
                            if (j == 4) c = '\n';
                            else c = ' ';
                            LogText += pos[i][j] + "" + c;
                        }
                    }
                    LogText += "\n";
                    Log.setText(LogText);

                    diffChessBoard(bd1,bd2);
                    for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd1[i][j]=bd2[i][j];
                    saveLog();
                    Log.setText(LogMsg);

                    break;
                }
            }
        }
    }
    private static void computerVsPlayer() throws IOException, InterruptedException {
        RandomChessSetting.removeActionListener(HandlerRandomChessSetting);
        ChessSetting.removeActionListener(HandlerChessSetting);
        DifficultySetting.removeActionListener(HandlerDifficultySetting);
        LogText += "游戏开始-机人对战\n";
        Log.setText(LogText);

        saveLog();
        Log.setText(LogMsg);

        JOptionPane.showMessageDialog(frame, "游戏开始-机人对战");
        String ipx;
        //int x = -1;
        boolean first = true;
        LogText += "电脑先手走棋：\n\n";
        Log.setText(LogText);

        saveLog();
        Log.setText(LogMsg);

        PlayerMove = true;
        int key=0;
        while (true) {
            int countkey=0;
            //print log
            PrintWriter LogPrinter = new PrintWriter("Log.txt");
            saveLog();
            LogPrinter.print(LogMsg);
            LogPrinter.close();
            if (over()) return;
            if (!PlayerMove) {
                //Die = random.nextInt(6) + 1;
                Die=0;
                while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                    ipx=JOptionPane.showInputDialog
                            (frame, "请输入骰子点数ֵ",
                                    "1-6", JOptionPane.PLAIN_MESSAGE);
                    try{
                        Die=Integer.parseInt(ipx);
                    }catch(Exception e){
                        Die=0;
                    }
                }
                PlayerLabel.setText("走棋方: 蓝方");
                DieLabel.setText("骰子点数: " + Die);
                //JOptionPane.showMessageDialog(null, "Your die:  " + Die);
                LogText += "Player's die: " + Die + "\n";
                Log.setText(LogText);

                saveLog();
                Log.setText(LogMsg);

                biaoJi();
            }

            int bd1[][] = new int[5][5];
            int bd2[][] = new int[5][5];
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    bd1[i][j] = 0;
                    for (int k = 1; k <= 6; k++) {
                        if (red[k][0] == i && red[k][1] == j) {
                            bd1[i][j] = k;
                            break;
                        }
                        if (blue[k][0] == i && blue[k][1] == j) {
                            bd1[i][j] = k + 6;
                            break;
                        }
                    }
                }
            }

            while (true) {
                Scanner input1 = new Scanner(System.in);
                if (PlayerMove) {
                    //System.out.println("ok");
                    int pos[][] = new int[5][5];
                    if (!first) {
                        for (int i = 0; i < 5; i++) {
                            for (int j = 0; j < 5; j++) {
                                pos[i][j] = 0;
                                for (int k = 1; k <= 6; k++) {
                                    if (red[k][0] == i && red[k][1] == j) {
                                        pos[i][j] = k;
                                        break;
                                    }
                                    if (blue[k][0] == i && blue[k][1] == j) {
                                        pos[i][j] = k + 6;
                                        break;
                                    }
                                }
                            }
                        }
                        for (int i = 0; i < 5; i++) {
                            for (int j = 0; j < 5; j++) {
                                char c;
                                if (j == 4) c = '\n';
                                else c = ' ';
                                LogText += pos[i][j] + "" + c;
                            }
                        }
                        LogText += "\n";
                        Log.setText(LogText);

                        for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd2[i][j]=pos[i][j];
                        diffChessBoard(bd1,bd2);
                        saveLog();
                        for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd1[i][j]=bd2[i][j];
                        Log.setText(LogMsg);

                    }
                    first = false;

                    if (over()) return;

                    //System.out.println("ok");
                    //Die = random.nextInt(6) + 1;
                    Die=0;
                    while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                        ipx=JOptionPane.showInputDialog
                                (frame, "请输入骰子点数ֵ",
                                        "1-6", JOptionPane.PLAIN_MESSAGE);
                        Die=Integer.parseInt(ipx);}
                    PlayerLabel.setText("走棋方: 红方");
                    DieLabel.setText("骰子点数: " + Die);
                    //JOptionPane.showMessageDialog(null, "Computer's die:  " + Die);
                    LogText += "Computer's die: " + Die + "\n";
                    Log.setText(LogText);

                    saveLog();
                    Log.setText(LogMsg);

                    PrintWriter output = new PrintWriter("JavaOut1.txt");
                    output.println(Difficulty + " " + Die);
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            int k;
                            for (k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    output.print(k);
                                    if (j != 4) output.print(" ");
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    output.print(k + 6);
                                    if (j != 4) output.print(" ");
                                    break;
                                }
                            }
                            if (k == 7) {
                                output.print(0);
                                if (j != 4) output.print(" ");
                            }
                        }
                        output.println();
                    }
                    PlayerMove = false;
                    output.close();


                    PrintWriter output3 = new PrintWriter("JavaOut.txt");
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            int k;
                            for (k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    output3.print(k);
                                    if (j != 4) output3.print(" ");
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    output3.print(k + 6);
                                    if (j != 4) output3.print(" ");
                                    break;
                                }
                            }
                            if (k == 7) {
                                output3.print(0);
                                if (j != 4) output3.print(" ");
                            }
                        }
                        output3.println();
                    }
                    output3.print(" "+Die);
                    output3.close();

//				PrintWriter output2 = new PrintWriter("Flag.txt");
//				output2.println("0");
//				output2.close();

//				Runtime Rt = Runtime.getRuntime();
//				File myfile = new File("EinsteinAI.exe");
//				Rt.exec(myfile.getAbsolutePath());


                    if(key==1) {Process p = Runtime.getRuntime().exec("EinsteinAI1.exe");
                        p.waitFor();}
                    if(key==0) {Process p = Runtime.getRuntime().exec("estin.exe");
                        p.waitFor();}
                    //System.out.println("ok2");
                    //System.out.println("ok1");
//				Scanner input2 = null;
//				int flag;
//				//while (flag == 0) {
//					input2 = new Scanner(Paths.get("Flag.txt"));
//					flag = input2.nextInt();
//					System.out.println("ok2");
//					input2.close();
//				//}
//				System.out.println(flag);
//
//				System.out.println("ok3");

                    Scanner input = new Scanner(Paths.get("JavaIn1.txt"));
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            pos[i][j] = input.nextInt();
                        }
                    }
                    input.close();

                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            if(pos[i][j]>0&&pos[i][j]<=6) {
                                countkey++;
                            }
                        }
                    }
                    if(countkey<=3) {key=1;}
				/*if(countkey==1) {
					key=0;
				}*/
                    for (int k = 1; k <= 6; k++) {
                        red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
                    }
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            //System.out.print(pos[i][j]);
                            //System.out.print(" ");
                            if (pos[i][j] >= 1 && pos[i][j] <= 6) {
                                red[pos[i][j]][0] = i;
                                red[pos[i][j]][1] = j;
                            }
                            if (pos[i][j] >= 7 && pos[i][j] <= 12) {
                                blue[pos[i][j] - 6][0] = i;
                                blue[pos[i][j] - 6][1] = j;
                            }
                        }
                        //System.out.println();
                    }
                    //System.out.println(blue[1][0] + " " + blue[1][1]);
                    //System.out.println(blue[2][0] + " " + blue[2][1]);

                    drawSituation();

                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            char c;
                            if (j == 4) c = '\n';
                            else c = ' ';
                            LogText += pos[i][j] + "" + c;
                        }
                    }
                    LogText += "\n";
                    Log.setText(LogText);


                    for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd2[i][j]=pos[i][j];
                    diffChessBoard(bd1,bd2);
                    saveLog();
                    for(int i=0;i<5;i++)for(int j=0;j<5;j++)bd1[i][j]=bd2[i][j];
                    Log.setText(LogMsg);

                    break;
                }
            }
        }
    }
    private static void playerVsPlayer() {
        String ipx;
        RandomChessSetting.removeActionListener(HandlerRandomChessSetting);
        ChessSetting.removeActionListener(HandlerChessSetting);
        DifficultySetting.removeActionListener(HandlerDifficultySetting);
        LogText += "游戏开始-人人对战\n\n";
        Log.setText(LogText);
        JOptionPane.showMessageDialog(frame, "游戏开始-人人对战");
        Player1Move = true;
        //Random random = new Random();
        while (true) {

            if (over()) return;

            //Die = random.nextInt(6) + 1;
            Die=0;
            while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                ipx=JOptionPane.showInputDialog
                        (frame, "请输入骰子点数",
                                "1-6", JOptionPane.PLAIN_MESSAGE);
                Die=Integer.parseInt(ipx);}
            PlayerLabel.setText("走棋方: 红方");
            DieLabel.setText("骰子点数: " + Die);
            //JOptionPane.showMessageDialog(null, "Player1's die:  " + Die);
            LogText += "Player1's die: " + Die + "\n";
            Log.setText(LogText);
            try {
                Thread.sleep(200);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            biaoJi();
            while (true) {
                Scanner input1 = new Scanner(System.in);
                if (!Player1Move) {
                    //System.out.println("ok");
                    int pos[][] = new int[5][5];
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            pos[i][j] = 0;
                            for (int k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    pos[i][j] = k;
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    pos[i][j] = k + 6;
                                    break;
                                }
                            }
                        }
                    }
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            char c;
                            if (j == 4) c = '\n';
                            else c = ' ';
                            LogText += pos[i][j] + "" + c;
                        }
                    }
                    LogText += "\n";
                    Log.setText(LogText);
                    if (over()) return;
                    break;
                }
            }

            //Die = random.nextInt(6) + 1;
            Die=0;
            while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                ipx=JOptionPane.showInputDialog
                        (frame, "请输入骰子点数",
                                "1-6", JOptionPane.PLAIN_MESSAGE);
                Die=Integer.parseInt(ipx);}
            PlayerLabel.setText("走棋方: 蓝方");
            DieLabel.setText("骰子点数: " + Die);
            //JOptionPane.showMessageDialog(null, "Player2's die:  " + Die);
            LogText += "Player2's die: " + Die + "\n";
            Log.setText(LogText);
            try {
                Thread.sleep(200);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            biaoJi();
            while (true) {
                Scanner input1 = new Scanner(System.in);
                if (Player1Move) {
                    //System.out.println("ok");
                    int pos[][] = new int[5][5];
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            pos[i][j] = 0;
                            for (int k = 1; k <= 6; k++) {
                                if (red[k][0] == i && red[k][1] == j) {
                                    pos[i][j] = k;
                                    break;
                                }
                                if (blue[k][0] == i && blue[k][1] == j) {
                                    pos[i][j] = k + 6;
                                    break;
                                }
                            }
                        }
                    }
                    for (int i = 0; i < 5; i++) {
                        for (int j = 0; j < 5; j++) {
                            char c;
                            if (j == 4) c = '\n';
                            else c = ' ';
                            LogText += pos[i][j] + "" + c;
                        }
                    }
                    LogText += "\n";
                    Log.setText(LogText);
                    if (over()) return;
                    break;
                }
            }
        }
    }
    private static void computerVsComputer() throws IOException, InterruptedException {
        String ipx;
        RandomChessSetting.removeActionListener(HandlerRandomChessSetting);
        ChessSetting.removeActionListener(HandlerChessSetting);
        DifficultySetting.removeActionListener(HandlerDifficultySetting);
        LogText += "游戏开始-机机对战\n\n";
        Log.setText(LogText);
        JOptionPane.showMessageDialog(frame, "游戏开始-机机对战");
        //Random random = new Random();
        while (true) {
            if (over()) return;
            //Die = random.nextInt(6) + 1;
            Die=0;
            while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                ipx=JOptionPane.showInputDialog
                        (frame, "请输入骰子点数ֵ",
                                "1-6", JOptionPane.PLAIN_MESSAGE);
                Die=Integer.parseInt(ipx);}
            PlayerLabel.setText("走棋方: 红方");
            DieLabel.setText("骰子点数: " + Die);
            //JOptionPane.showMessageDialog(null, "Computer1's die:  " + Die);
            LogText += "Computer1's die: " + Die + "\n";
            Log.setText(LogText);
            PrintWriter output1 = new PrintWriter("JavaOut1.txt");
            //output1.println(Difficulty + " " + Die);
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    int k;
                    for (k = 1; k <= 6; k++) {
                        if (red[k][0] == i && red[k][1] == j) {
                            output1.print(k);
                            if (j != 4)
                                output1.print(" ");
                            break;
                        }
                        if (blue[k][0] == i && blue[k][1] == j) {
                            output1.print(k + 6);
                            if (j != 4)
                                output1.print(" ");
                            break;
                        }
                    }
                    if (k == 7) {
                        output1.print(0);
                        if (j != 4)
                            output1.print(" ");
                    }
                }
                output1.println();
            }
            output1.print(" "+Die);
            output1.close();
            //Process p1 = Runtime.getRuntime().exec("EinsteinAI1.exe");
            Process p1 = Runtime.getRuntime().exec("estin.exe");
            p1.waitFor();
            Scanner input1 = new Scanner(Paths.get("JavaIn1.txt"));
            int pos1[][] = new int[5][5];
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    pos1[i][j] = input1.nextInt();
                }
            }
            input1.close();
            for (int k = 1; k <= 6; k++) {
                red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
            }
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    // System.out.print(pos[i][j]);
                    // System.out.print(" ");
                    if (pos1[i][j] >= 1 && pos1[i][j] <= 6) {
                        red[pos1[i][j]][0] = i;
                        red[pos1[i][j]][1] = j;
                    }
                    if (pos1[i][j] >= 7 && pos1[i][j] <= 12) {
                        blue[pos1[i][j] - 6][0] = i;
                        blue[pos1[i][j] - 6][1] = j;
                    }
                }
                //System.out.println();
            }
            drawSituation();

            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    char c;
                    if (j == 4) c = '\n';
                    else c = ' ';
                    LogText += pos1[i][j] + "" + c;
                }
            }
            LogText += "\n";
            Log.setText(LogText);

            if (over()) return;
            //Die = random.nextInt(6) + 1;
            Die=0;
            while(!(Die == 1 || Die == 2 || Die == 3 || Die == 4 || Die == 5 || Die == 6)){
                ipx=JOptionPane.showInputDialog
                        (frame, "请输入骰子点数ֵ",
                                "1-6", JOptionPane.PLAIN_MESSAGE);
                Die=Integer.parseInt(ipx);}
            PlayerLabel.setText("走棋方: 蓝方");
            DieLabel.setText("骰子点数: " + Die);
            //JOptionPane.showMessageDialog(null, "Computer2's die:  " + Die);
            LogText += "Computer1's die: " + Die + "\n";
            Log.setText(LogText);
            PrintWriter output2 = new PrintWriter("JavaOut.txt");
            output2.println(Difficulty + " " + Die);
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    int k;
                    for (k = 1; k <= 6; k++) {
                        if (red[k][0] == i && red[k][1] == j) {
                            output2.print(k);
                            if (j != 4)
                                output2.print(" ");
                            break;
                        }
                        if (blue[k][0] == i && blue[k][1] == j) {
                            output2.print(k + 6);
                            if (j != 4)
                                output2.print(" ");
                            break;
                        }
                    }
                    if (k == 7) {
                        output2.print(0);
                        if (j != 4)
                            output2.print(" ");
                    }
                }
                output2.println();
            }
            output2.close();
            Process p2 = Runtime.getRuntime().exec("EinsteinAI.exe");
            p2.waitFor();
            Scanner input2 = new Scanner(Paths.get("JavaIn.txt"));
            int pos2[][] = new int[5][5];
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    pos2[i][j] = input2.nextInt();
                }
            }
            input2.close();
            for (int k = 1; k <= 6; k++) {
                red[k][0] = red[k][1] = blue[k][0] = blue[k][1] = -1;
            }
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    // System.out.print(pos[i][j]);
                    // System.out.print(" ");
                    if (pos2[i][j] >= 1 && pos2[i][j] <= 6) {
                        red[pos2[i][j]][0] = i;
                        red[pos2[i][j]][1] = j;
                    }
                    if (pos2[i][j] >= 7 && pos2[i][j] <= 12) {
                        blue[pos2[i][j] - 6][0] = i;
                        blue[pos2[i][j] - 6][1] = j;
                    }
                }
                //System.out.println();
            }
            drawSituation();
            for (int i = 0; i < 5; i++) {
                for (int j = 0; j < 5; j++) {
                    char c;
                    if (j == 4) c = '\n';
                    else c = ' ';
                    LogText += pos1[i][j] + "" + c;
                }
            }
            LogText += "\n";
            Log.setText(LogText);
        }
    }
    public static void haveFun() throws InterruptedException, IOException {
        ChessBoard chessboard = new ChessBoard();
        while (true) {
            initialize();
            frame.setVisible(true);
            while (true) {
                Scanner input2 = new Scanner(System.in);
                if (Mode == 1) {
                    playerVsComputer();
                    Mode = 0;
                    break;
                }
                if (Mode == 2) {
                    playerVsPlayer();
                    Mode = 0;
                    break;
                }
                if (Mode == 3) {
                    computerVsPlayer();
                    Mode = 0;
                    break;
                }
            }
            frame.setVisible(false);
        }
    }
    public static void drawSituation() {

        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                frame.getContentPane().remove(panel[i][j]);
                if ((5 * i + j) % 2 == 0) {
                    panel[i][j] = new JPanelGrey();
                }
                else {
                    panel[i][j] = new JPanelWhite();
                }
                panel[i][j].setBounds(10 + j * 80, 10 + i * 80, 80, 80);
                frame.getContentPane().add(panel[i][j]);
                panel[i][j].repaint();
            }
        }

        for (int k = 1; k <= 6; k++) {
            int x, y;

            if (red[k][0] != -1 && red[k][1] != -1) {
                x = red[k][0]; y = red[k][1];
                frame.getContentPane().remove(panel[x][y]);
                if ((5 * x + y) % 2 == 0) {
                    panel[x][y] = new JPanelGreyChess(0, k);
                }
                else {
                    panel[x][y] = new JPanelWhiteChess(0, k);
                }
                panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                frame.getContentPane().add(panel[x][y]);
                panel[x][y].repaint();
            }

            if (blue[k][0] != -1 && blue[k][1] != -1) {
                x = blue[k][0]; y = blue[k][1];
                frame.getContentPane().remove(panel[x][y]);
                if ((5 * x + y) % 2 == 0) {
                    panel[x][y] = new JPanelGreyChess(1, k);
                }
                else {
                    panel[x][y] = new JPanelWhiteChess(1, k);
                }
                panel[x][y].setBounds(10 + y * 80, 10 + x * 80, 80, 80);
                frame.getContentPane().add(panel[x][y]);
                panel[x][y].repaint();
            }

        }

        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                panel[i][j].removeMouseListener(HandlerSelect);
                panel[i][j].removeMouseListener(HandlerMove);
                panel[i][j].removeMouseListener(HandlerFailMove);
            }
        }
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                for (int k = 1; k <= 6; k++) {
                    if ((red[k][0] == i && red[k][1] == j)
                            || (blue[k][0] == i && blue[k][1] == j)) {
                        panel[i][j].addMouseListener(HandlerSelect);
                        break;
                    }
                }
            }
        }
    }

}

class JPanelGrey extends JPanel {

    public void paint(Graphics g){
        try {
            g.clearRect(0, 0, 80, 80);
            g.setColor(Color.GRAY);
            g.fillRect(0, 0, 80, 80);

        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
}

class JPanelWhite extends JPanel {

    public void paint(Graphics g){
        try {
            g.clearRect(0, 0, 80, 80);
            g.setColor(new Color(211, 211, 211));
            g.fillRect(0, 0, 80, 80);
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

}

class JPanelGreyChess extends JPanel {

    Image image = null;
    public int Colour, Number;

    JPanelGreyChess(int c, int n) {
        super();
        Colour = c;
        Number = n;
    }

    public void paint(Graphics g){
        try {
            //System.out.println("ok2");
            g.setColor(Color.GRAY);
            if (Colour > 1) g.setColor(Color.YELLOW);
            g.fillRect(0, 0, 80, 80);
            String FileName = "";
            if (Colour == 0 || Colour == 2) FileName += "red";
            else FileName += "blue";
            FileName += Number;
            FileName += ".png";
            image=ImageIO.read(new File(FileName));
            g.drawImage(image, 5, 5, 70, 70, null);
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
}

class JPanelWhiteChess extends JPanel {

    Image image = null;
    public int Colour, Number;

    JPanelWhiteChess(int c, int n) {
        super();
        Colour = c;
        Number = n;
    }

    public void paint(Graphics g){
        try {
            //System.out.println("ok2");
            g.setColor(new Color(211, 211, 211));
            if (Colour > 1) g.setColor(Color.YELLOW);
            g.fillRect(0, 0, 80, 80);
            String FileName = "";
            if (Colour == 0 || Colour == 2) FileName += "red";
            else FileName += "blue";
            FileName += Number;
            FileName += ".png";
            image=ImageIO.read(new File(FileName));
            g.drawImage(image, 5, 5, 70, 70, null);
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }
}