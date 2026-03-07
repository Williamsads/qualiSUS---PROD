from flask import Blueprint, render_template, request, redirect, session, flash, url_for, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from app.database import get_connection

ppp_bp = Blueprint('ppp', __name__)


@ppp_bp.route('/ppp')
def gestao_ppp():
    if "user_id" not in session:
        return redirect(url_for('raiz'))
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Busca básica para a lista
    query = """
        SELECT p.*, 
               u1.nome as criado_por_nome, u2.nome as assinado_por_nome
        FROM ppp p
        LEFT JOIN usuarios u1 ON p.criado_por = u1.id
        LEFT JOIN usuarios u2 ON p.assinado_por = u2.id
        WHERE p.ativo = TRUE
        ORDER BY p.data_criacao DESC
    """
    cursor.execute(query)
    ppps = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('gestao_ppp.html', ppps=ppps, nome=session.get('nome'), tipo=session.get('tipo'))

@ppp_bp.route('/ppp/novo')
def novo_ppp():
    if "user_id" not in session:
        return redirect(url_for('raiz'))
    
    return render_template('form_ppp.html', action='Criar', ppp=None, 
                           today=datetime.now().strftime('%Y-%m-%d'), 
                           nome=session.get('nome'), tipo=session.get('tipo'))


@ppp_bp.route('/ppp/historico/<int:id>')
def historico_ppp(id):
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT h.*, u.nome as usuario_nome
        FROM ppp_historico h
        LEFT JOIN usuarios u ON h.usuario_id = u.id
        WHERE h.ppp_id = %s
        ORDER BY h.data DESC
    """, (id,))
    historico = cursor.fetchall()
    
    # Tratamento de data para JSON
    for item in historico:
        item['data'] = item['data'].strftime('%d/%m/%Y %H:%M')
        
    cursor.close()
    conn.close()
    
    return jsonify(historico)

@ppp_bp.route('/ppp/editar/<int:id>')
def editar_ppp(id):
    if "user_id" not in session:
        return redirect(url_for('raiz'))
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM ppp WHERE id = %s", (id,))
    ppp = cursor.fetchone()
    
    if not ppp:
        flash("PPP não encontrado.", "error")
        return redirect(url_for('ppp.gestao_ppp'))
        
    if ppp['status'] == 'ASSINADO':
        flash("Este PPP já está assinado e não pode ser editado.", "warning")
        return redirect(url_for('ppp.gestao_ppp'))

    # Buscar dados das sub-tabelas
    cursor.execute("SELECT * FROM ppp_lotacao WHERE ppp_id = %s", (id,))
    lotacao = cursor.fetchall()
    
    cursor.execute("SELECT * FROM ppp_profissiografia WHERE ppp_id = %s", (id,))
    profissiografia = cursor.fetchall()
    
    cursor.execute("SELECT * FROM ppp_registros_ambientais WHERE ppp_id = %s", (id,))
    ambiental = cursor.fetchall()
    
    cursor.execute("SELECT * FROM ppp_responsaveis_registros WHERE ppp_id = %s", (id,))
    responsaveis = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('form_ppp.html', action='Editar', ppp=ppp, 
                           lotacao=lotacao, profissiografia=profissiografia, 
                           ambiental=ambiental, responsaveis=responsaveis,
                           today=datetime.now().strftime('%Y-%m-%d'), 
                           nome=session.get('nome'), tipo=session.get('tipo'))

@ppp_bp.route('/ppp/salvar', methods=['POST'])
def salvar_ppp():
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    ppp_id = data.get('id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if ppp_id:
            # Update existing header
            cursor.execute("""
                UPDATE ppp SET 
                    cnpj_empresa = %s, nome_empresarial = %s, cnae = %s, br_pdh = %s, 
                    data_admissao = %s, nome_trabalhador = %s, cpf_trabalhador = %s, 
                    data_nascimento = %s, sexo = %s, matricula_trabalhador = %s, 
                    cargo_trabalhador = %s, unidade_trabalhador = %s, regime_revezamento = %s,
                    cat_data_registro = %s, cat_numero = %s, data_emissao = %s, 
                    rep_legal_nome = %s, rep_legal_cpf = %s, observacoes = %s
                WHERE id = %s
            """, (data.get('cnpj_empresa'), data.get('nome_empresarial'), data.get('cnae'), data.get('br_pdh'), 
                  data.get('data_admissao') or None, data.get('nome_trabalhador'), data.get('cpf_trabalhador'), 
                  data.get('data_nascimento') or None, data.get('sexo'), data.get('matricula_trabalhador'), 
                  data.get('cargo_trabalhador'), data.get('unidade_trabalhador'), data.get('regime_revezamento'),
                  data.get('cat_data_registro') or None, data.get('cat_numero'), data.get('data_emissao'), 
                  data.get('rep_legal_nome'), data.get('rep_legal_cpf'), data.get('observacoes'), ppp_id))
            
            # Log history
            cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                           (ppp_id, session['user_id'], 'PPP Editado', 'O documento foi atualizado.'))
            
            # Clear existing sub-records to replace them (simplifies sync)
            cursor.execute("DELETE FROM ppp_lotacao WHERE ppp_id = %s", (ppp_id,))
            cursor.execute("DELETE FROM ppp_profissiografia WHERE ppp_id = %s", (ppp_id,))
            cursor.execute("DELETE FROM ppp_registros_ambientais WHERE ppp_id = %s", (ppp_id,))
            cursor.execute("DELETE FROM ppp_responsaveis_registros WHERE ppp_id = %s", (ppp_id,))
        else:
            # Create new - manual entry
            cursor.execute("""
                INSERT INTO ppp (
                    cnpj_empresa, nome_empresarial, cnae, br_pdh, data_admissao,
                    nome_trabalhador, cpf_trabalhador, data_nascimento, sexo, 
                    matricula_trabalhador, cargo_trabalhador, unidade_trabalhador,
                    regime_revezamento, cat_data_registro, cat_numero,
                    criado_por, status, data_criacao
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ELABORACAO', NOW()) RETURNING id
            """, (data.get('cnpj_empresa'), data.get('nome_empresarial'), data.get('cnae'), data.get('br_pdh'),
                  data.get('data_admissao') or None, data.get('nome_trabalhador'), data.get('cpf_trabalhador'), 
                  data.get('data_nascimento') or None, data.get('sexo'), data.get('matricula_trabalhador'), 
                  data.get('cargo_trabalhador'), data.get('unidade_trabalhador'), data.get('regime_revezamento'),
                  data.get('cat_data_registro') or None, data.get('cat_numero'), session['user_id']))
            ppp_id = cursor.fetchone()[0]
            
            # Log history
            cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                           (ppp_id, session['user_id'], 'PPP Criado', 'Iniciado novo documento.'))
            
        # Insert Lotação
        for item in data.get('lotacao', []):
            if any(item.values()): # Only if not empty
                cursor.execute("""
                    INSERT INTO ppp_lotacao (ppp_id, periodo_inicio, periodo_fim, cnpj, setor, cargo, funcao, cbo, gfip)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ppp_id, item.get('periodo_inicio') or None, item.get('periodo_fim') or None, item.get('cnpj'), 
                      item.get('setor'), item.get('cargo'), item.get('funcao'), item.get('cbo'), item.get('gfip')))

        # Insert Profissiografia
        for item in data.get('profissiografia', []):
            if any(item.values()):
                cursor.execute("""
                    INSERT INTO ppp_profissiografia (ppp_id, periodo_inicio, periodo_fim, descricao)
                    VALUES (%s, %s, %s, %s)
                """, (ppp_id, item.get('periodo_inicio') or None, item.get('periodo_fim') or None, item.get('descricao')))

        # Insert Ambiental
        for item in data.get('ambiental', []):
            if any(item.values()):
                cursor.execute("""
                    INSERT INTO ppp_registros_ambientais (
                        ppp_id, periodo_inicio, periodo_fim, tipo, fator_risco, 
                        intensidade, tecnica, epc_eficaz, epi_eficaz, ca_epi,
                        medida_protecao, condicao_funcionamento, prazo_validade_epi, 
                        periodicidade_troca_epi, higienizacao_epi
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ppp_id, item.get('periodo_inicio') or None, item.get('periodo_fim') or None, item.get('tipo'), 
                      item.get('fator_risco'), item.get('intensidade'), item.get('tecnica'), item.get('epc_eficaz'), 
                      item.get('epi_eficaz'), item.get('ca_epi'), item.get('medida_protecao'), 
                      item.get('condicao_funcionamento'), item.get('prazo_validade_epi'), 
                      item.get('periodicidade_troca_epi'), item.get('higienizacao_epi')))

        # Insert Responsáveis
        for item in data.get('responsaveis', []):
            if any(item.values()):
                cursor.execute("""
                    INSERT INTO ppp_responsaveis_registros (ppp_id, periodo_inicio, periodo_fim, cpf, registro_conselho, nome)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (ppp_id, item.get('periodo_inicio') or None, item.get('periodo_fim') or None, item.get('cpf'), item.get('registro_conselho'), item.get('nome')))

        conn.commit()
        return jsonify({'success': True, 'id': ppp_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@ppp_bp.route('/ppp/finalizar/<int:id>', methods=['POST'])
def finalizar_ppp(id):
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE ppp SET status = 'FINALIZADO', finalizado_por = %s, data_finalizacao = NOW()
            WHERE id = %s
        """, (session['user_id'], id))
        
        cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                       (id, session['user_id'], 'PPP Finalizado', 'Documento marcado como finalizado para assinatura.'))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@ppp_bp.route('/ppp/assinar/<int:id>', methods=['POST'])
def assinar_ppp(id):
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # In a real scenario, we would check if session['tipo'] allows signing
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE ppp SET status = 'ASSINADO', assinado_por = %s, data_assinatura = NOW()
            WHERE id = %s
        """, (session['user_id'], id))
        
        cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                       (id, session['user_id'], 'PPP Assinado', 'Documento assinado digitalmente.'))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
@ppp_bp.route('/ppp/republicar/<int:id>', methods=['POST'])
def republicar_ppp(id):
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    motivo = data.get('motivo')
    
    if not motivo:
        return jsonify({'error': 'O motivo da republicação é obrigatório.'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Fetch original PPP
        cursor.execute("SELECT * FROM ppp WHERE id = %s", (id,))
        old_ppp = cursor.fetchone()
        
        if not old_ppp:
            return jsonify({'error': 'PPP não encontrado.'}), 404
            
        # 2. Create new version
        cursor.execute("""
            INSERT INTO ppp (
                cnpj_empresa, nome_empresarial, cnae, br_pdh, data_admissao,
                nome_trabalhador, cpf_trabalhador, data_nascimento, sexo, 
                matricula_trabalhador, cargo_trabalhador, unidade_trabalhador,
                regime_revezamento, cat_data_registro, cat_numero,
                data_emissao, rep_legal_nome, rep_legal_cpf, observacoes,
                criado_por, status, data_criacao, parent_id, motivo_republicacao
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ELABORACAO', NOW(), %s, %s) 
            RETURNING id
        """, (old_ppp['cnpj_empresa'], old_ppp['nome_empresarial'], old_ppp['cnae'], old_ppp['br_pdh'], old_ppp['data_admissao'],
              old_ppp['nome_trabalhador'], old_ppp['cpf_trabalhador'], old_ppp['data_nascimento'],
              old_ppp['sexo'], old_ppp['matricula_trabalhador'], old_ppp['cargo_trabalhador'],
              old_ppp['unidade_trabalhador'], old_ppp['regime_revezamento'], old_ppp['cat_data_registro'], old_ppp['cat_numero'],
              old_ppp['data_emissao'], old_ppp['rep_legal_nome'], old_ppp['rep_legal_cpf'], old_ppp['observacoes'],
              session['user_id'], id, motivo))
        
        new_id = cursor.fetchone()['id']
        
        # 3. Clone sub-tables
        # 3.1 Lotação
        cursor.execute("SELECT * FROM ppp_lotacao WHERE ppp_id = %s", (id,))
        for item in cursor.fetchall():
            cursor.execute("""
                INSERT INTO ppp_lotacao (ppp_id, periodo_inicio, periodo_fim, cnpj, setor, cargo, funcao, cbo, gfip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id, item['periodo_inicio'], item['periodo_fim'], item['cnpj'], item['setor'], item['cargo'], item['funcao'], item['cbo'], item['gfip']))
            
        # 3.2 Profissiografia
        cursor.execute("SELECT * FROM ppp_profissiografia WHERE ppp_id = %s", (id,))
        for item in cursor.fetchall():
            cursor.execute("""
                INSERT INTO ppp_profissiografia (ppp_id, periodo_inicio, periodo_fim, descricao)
                VALUES (%s, %s, %s, %s)
            """, (new_id, item['periodo_inicio'], item['periodo_fim'], item['descricao']))
            
        # 3.3 Ambiental
        cursor.execute("SELECT * FROM ppp_registros_ambientais WHERE ppp_id = %s", (id,))
        for item in cursor.fetchall():
            cursor.execute("""
                INSERT INTO ppp_registros_ambientais (
                    ppp_id, periodo_inicio, periodo_fim, tipo, fator_risco, 
                    intensidade, tecnica, epc_eficaz, epi_eficaz, ca_epi,
                    medida_protecao, condicao_funcionamento, prazo_validade_epi, 
                    periodicidade_troca_epi, higienizacao_epi
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_id, item['periodo_inicio'], item['periodo_fim'], item['tipo'], 
                  item['fator_risco'], item['intensidade'], item['tecnica'], item['epc_eficaz'], 
                  item['epi_eficaz'], item['ca_epi'], item['medida_protecao'], 
                  item['condicao_funcionamento'], item['prazo_validade_epi'], 
                  item['periodicidade_troca_epi'], item['higienizacao_epi']))
            
        # 3.4 Responsáveis
        cursor.execute("SELECT * FROM ppp_responsaveis_registros WHERE ppp_id = %s", (id,))
        for item in cursor.fetchall():
            cursor.execute("""
                INSERT INTO ppp_responsaveis_registros (ppp_id, periodo_inicio, periodo_fim, cpf, registro_conselho, nome)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (new_id, item['periodo_inicio'], item['periodo_fim'], item['cpf'], item['registro_conselho'], item['nome']))
            
        # 4. Update old PPP to inactive (optional, or just track via parent_id)
        # cursor.execute("UPDATE ppp SET ativo = FALSE WHERE id = %s", (id,))
        
        # 5. Log history
        cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                       (new_id, session['user_id'], 'Republicação Criada', f'Nova versão baseada no PPP #{id}. Motivo: {motivo}'))
        
        cursor.execute("INSERT INTO ppp_historico (ppp_id, usuario_id, acao, descricao) VALUES (%s, %s, %s, %s)",
                       (id, session['user_id'], 'Documento Republicado', f'Gerada nova versão (PPP #{new_id}).'))
        
        conn.commit()
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
