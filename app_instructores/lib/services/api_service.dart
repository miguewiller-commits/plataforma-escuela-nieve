import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

class ApiService {
  // Para web, localhost:
  static String baseUrl = 'http://127.0.0.1:8000';

  static String? accessToken;
  static String? refreshToken;

  // =====================================================
  // 🔹 LOGIN INSTRUCTOR
  // Django espera: { correo, password }
  // =====================================================
  static Future<bool> login(String correo, String password) async {
    final url = Uri.parse('$baseUrl/api/instructor/login/');

    final resp = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'correo': correo,
        'password': password,
      }),
    );

    print('LOGIN status: ${resp.statusCode}');
    print('LOGIN body: ${resp.body}');

    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);

      accessToken = data['access'];
      refreshToken = data['refresh'];

      print("TOKEN GUARDADO:");
      print("access: $accessToken");
      print("refresh: $refreshToken");

      return true;
    }

    return false;
  }

  // =====================================================
  // 🔹 OBTENER CLASES DEL INSTRUCTOR (sin fecha)
  // =====================================================
  static Future<List<dynamic>> fetchClases() async {
    final url = Uri.parse('$baseUrl/api/instructor/clases/');

    final resp = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      },
    );

    print('CLASES status: ${resp.statusCode}');
    print('CLASES body: ${resp.body}');

    return jsonDecode(resp.body) as List;
  }

  // =====================================================
  // 🔹 OBTENER CLASES POR FECHA
  // Django espera: YYYY-MM-DD
  // =====================================================
  static Future<List<dynamic>> fetchClasesForDate(DateTime fecha) async {
    final f = DateFormat('yyyy-MM-dd').format(fecha);

    final url =
        Uri.parse('$baseUrl/api/instructor/clases/?fecha=$f');

    final resp = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      },
    );

    print('CLASES FECHA status: ${resp.statusCode}');
    print('CLASES FECHA body: ${resp.body}');

    if (resp.statusCode == 200) {
      return jsonDecode(resp.body) as List;
    } else {
      throw Exception(
          'Error ${resp.statusCode}: ${resp.body}');
    }
  }
}
