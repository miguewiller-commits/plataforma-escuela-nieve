import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:intl/intl.dart';

class ApiService {
  static final _supabase = Supabase.instance.client;

  // =====================================================
  // 🔹 LOGIN INSTRUCTOR
  // =====================================================
  static Future<bool> login(String correo, String password) async {
    try {
      final AuthResponse res = await _supabase.auth.signInWithPassword(
        email: correo,
        password: password,
      );
      return res.user != null && res.session != null;
    } catch (e) {
      print('Error de Login: $e');
      return false;
    }
  }

  // =====================================================
  // 🔹 LOGOUT
  // =====================================================
  static Future<void> logout() async {
    await _supabase.auth.signOut();
  }

  // =====================================================
  // 🔹 OBTENER CLASES (CORREGIDO)
  // =====================================================
  static Future<List<Map<String, dynamic>>> fetchClases({DateTime? fecha}) async {
    try {
      final userId = _supabase.auth.currentUser?.id;
      if (userId == null) throw Exception('No hay usuario autenticado');

      // 1. Iniciamos la consulta (Sin ordenar todavía)
      // Esto nos devuelve un 'PostgrestFilterBuilder' que SÍ acepta .gte/.lte
      var query = _supabase.from('clases_clase').select();

      // 2. Aplicamos filtros condicionales
      if (fecha != null) {
        // Rango del día completo
        final start = DateTime(fecha.year, fecha.month, fecha.day).toIso8601String();
        final end = DateTime(fecha.year, fecha.month, fecha.day, 23, 59, 59).toIso8601String();
        
        // Ahora sí podemos usar .gte y .lte
        query = query.gte('hora_inicio', start).lte('hora_inicio', end);
      }

      // 3. Aplicamos el ordenamiento al FINAL
      // .order() devuelve un 'PostgrestTransformBuilder', por eso debe ir último
      final res = await query.order('hora_inicio', ascending: true);
      
      return List<Map<String, dynamic>>.from(res);
      
    } catch (e) {
      print('Error obteniendo clases: $e');
      return [];
    }
  }
}