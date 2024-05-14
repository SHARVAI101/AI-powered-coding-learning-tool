public class MyClass {

public static void main(String args[]) {
     System.out.println(reverseString("hello"));
} 

public static String reverseString(String str) {
    char[] chars = new char[str.length()];
    for (int i = 0; i < str.length(); i++) {
        chars[i] = str.charAt(str.length() - 1 - i);
    }
    return new String(chars);
}

}